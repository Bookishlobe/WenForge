"""事实验证器 —— 检测新旧事实之间的冲突

冲突判定规则:
1. CRITICAL: 同实体+同属性+不同值，且值之间有不可逆变化（如死亡→复活、修为倒退）
2. WARNING: 同实体+同属性+不同值，但可能是合理演进
3. INFO: 新信息，无冲突
"""

from __future__ import annotations

import logging
from typing import Optional

from .models import FactTriple, Conflict, ConflictSeverity

logger = logging.getLogger("wenforge.fact_engine.verifier")

# 不可逆的状态变化（旧值→新值的矛盾方向）
_IRREVERSIBLE_TRANSITIONS: dict[str, set[str]] = {
    "状态": {"已死亡"},
}

# 正常前进方向（旧值→新值，不是矛盾，是演进）
_PROGRESSION_PATTERNS: dict[str, list[list[str]]] = {
    "修为": [
        ["练气期", "筑基期", "金丹期", "元婴期", "化神期", "合体期", "大乘期", "渡劫期"],
        ["初期", "中期", "后期", "巅峰", "圆满"],
        ["一阶", "二阶", "三阶", "四阶", "五阶", "六阶", "七阶", "八阶", "九阶"],
    ],
}


class FactVerifier:
    """检测新旧事实之间的冲突。"""

    def verify(
        self,
        incoming: FactTriple,
        existing_triples: list[FactTriple],
    ) -> Optional[Conflict]:
        """验证一条新事实是否与已有事实冲突。

        Returns:
            Conflict 对象（有冲突时），None（无冲突时）
        """
        matches = [t for t in existing_triples if t.key == incoming.key]

        if not matches:
            return None

        latest = max(matches, key=lambda t: t.chapter)

        if latest.value == incoming.value:
            return None

        severity = self._classify_conflict(latest, incoming)

        return Conflict(
            existing=latest,
            incoming=incoming,
            severity=severity,
            description=(
                f"{incoming.subject} 的 {incoming.attribute} 从 "
                f"'{latest.value}'(第{latest.chapter}章) "
                f"变为 '{incoming.value}'(第{incoming.chapter}章)"
            ),
        )

    def verify_batch(
        self,
        incoming_triples: list[FactTriple],
        existing_triples: list[FactTriple],
    ) -> tuple[list[Conflict], list[FactTriple]]:
        """批量验证，返回冲突列表和新事实列表"""
        conflicts: list[Conflict] = []
        new_triples: list[FactTriple] = []

        for t in incoming_triples:
            conflict = self.verify(t, existing_triples)
            if conflict:
                conflicts.append(conflict)
            else:
                new_triples.append(t)

        logger.info(
            f"验证 {len(incoming_triples)} 条事实: "
            f"{len(conflicts)} 冲突, {len(new_triples)} 新事实"
        )
        return conflicts, new_triples

    def _classify_conflict(
        self, old: FactTriple, new: FactTriple
    ) -> ConflictSeverity:
        """判定冲突严重度"""
        attr = old.attribute
        old_val = old.value
        new_val = new.value

        # 检查不可逆状态
        irreversible = _IRREVERSIBLE_TRANSITIONS.get(attr, set())
        if old_val in irreversible and new_val not in irreversible:
            return ConflictSeverity.CRITICAL

        # 检查是否正常演进
        if self._is_progression(attr, old_val, new_val):
            return ConflictSeverity.INFO

        # 检查是否倒退
        if self._is_regression(attr, old_val, new_val):
            return ConflictSeverity.CRITICAL if old.confidence > 0.8 else ConflictSeverity.WARNING

        return ConflictSeverity.WARNING

    def _is_progression(self, attr: str, old_val: str, new_val: str) -> bool:
        """判断是否为正常的前进（如修为升级）"""
        sequences = _PROGRESSION_PATTERNS.get(attr, [])
        for seq in sequences:
            if old_val in seq and new_val in seq:
                return seq.index(new_val) > seq.index(old_val)
        return False

    def _is_regression(self, attr: str, old_val: str, new_val: str) -> bool:
        """判断是否为倒退（如修为下降）"""
        sequences = _PROGRESSION_PATTERNS.get(attr, [])
        for seq in sequences:
            if old_val in seq and new_val in seq:
                return seq.index(new_val) < seq.index(old_val)
        return False
