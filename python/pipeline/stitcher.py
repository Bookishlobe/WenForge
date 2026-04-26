"""一致性缝合器 —— 跨章节事实冲突检测与修复

工作流:
  1. 从所有已生成章节提取事实三元组
  2. 检测新旧事实之间的冲突（死亡→复活, 修为倒退等）
  3. 按严重级别分类: CRITICAL(必须修复) / WARNING(建议修复) / INFO(提示)
  4. 生成修复指令: 重写段落、修正描述、添加过渡解释
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from .models import PipelineState
from fact_engine.models import FactTriple, Conflict, ConflictSeverity, ChapterFacts
from fact_engine.extractor import FactExtractor
from fact_engine.verifier import FactVerifier
from fact_engine.triple_store import TripleStore

logger = logging.getLogger("wenforge.pipeline.stitcher")

FIXER_SYSTEM = (
    "你是一位专业的中国网络小说编辑，擅长在保持写作风格的前提下"
    "修复前后章节的事实矛盾。只修改存在矛盾的具体段落，不要大改。"
)


class StitchResult:
    """缝合结果"""

    def __init__(self):
        self.conflicts: list[Conflict] = []
        self.critical: list[Conflict] = []
        self.warnings: list[Conflict] = []
        self.infos: list[Conflict] = []
        self.fix_count: int = 0
        self.total_words_changed: int = 0

    @property
    def is_clean(self) -> bool:
        return len(self.critical) == 0 and len(self.warnings) == 0

    @property
    def summary(self) -> str:
        return (
            f"缝合完成: {len(self.conflicts)}冲突 "
            f"(严重{len(self.critical)}/警告{len(self.warnings)}/提示{len(self.infos)}), "
            f"修复{self.fix_count}处, 变更{self.total_words_changed}字"
        )


class Stitcher:
    """跨章节一致性缝合。"""

    def __init__(
        self,
        provider: Any = None,
        extractor: Optional[FactExtractor] = None,
        verifier: Optional[FactVerifier] = None,
        store: Optional[TripleStore] = None,
        book_id: str = "",
    ):
        self.provider = provider
        self.extractor = extractor or FactExtractor(provider)
        self.verifier = verifier or FactVerifier()
        self.store = store or TripleStore()
        self.book_id = book_id

    def stitch(
        self, chapter_texts: dict[int, str], state: PipelineState
    ) -> tuple[dict[int, str], StitchResult]:
        """缝合所有章节，检测并修复冲突。"""
        result = StitchResult()
        chapter_facts_map: dict[int, ChapterFacts] = {}

        # Phase 1: 提取所有章节事实
        logger.info(f"开始提取 {len(chapter_texts)} 章事实...")
        for idx, text in sorted(chapter_texts.items()):
            cf = self.extractor.extract(text, idx)
            chapter_facts_map[idx] = cf
            self.store.save_chapter(self.book_id, cf)

        # 加载已有事实（历史章节）
        existing = self.store.load_all(self.book_id, max_chapters=max(chapter_texts.keys()))
        min_idx = min(chapter_texts.keys()) if chapter_texts else 1
        existing = [t for t in existing if t.chapter < min_idx]
        logger.info(f"历史事实 {len(existing)} 条，当前批次 {min_idx}+")

        # Phase 2: 按章节顺序检测冲突
        all_known = list(existing)
        fixed_texts = dict(chapter_texts)

        for idx in sorted(chapter_texts.keys()):
            cf = chapter_facts_map.get(idx)
            if cf is None:
                continue

            conflicts, new_triples = self.verifier.verify_batch(cf.triples, all_known)
            all_known.extend(new_triples)

            for c in conflicts:
                result.conflicts.append(c)
                if c.severity == ConflictSeverity.CRITICAL:
                    result.critical.append(c)
                elif c.severity == ConflictSeverity.WARNING:
                    result.warnings.append(c)
                else:
                    result.infos.append(c)

            # Phase 3: 修复 CRITICAL 冲突（有 provider 时）
            if result.critical and self.provider is not None:
                text = fixed_texts.get(idx, "")
                fixed_text, changes = self._fix_conflicts(
                    idx, text, result.critical
                )
                if fixed_text != text:
                    fixed_texts[idx] = fixed_text
                    result.fix_count += 1
                    result.total_words_changed += changes
                result.critical.clear()

        if not result.is_clean:
            state.errors.append(result.summary)

        logger.info(result.summary)
        return fixed_texts, result

    def _fix_conflicts(
        self, chapter_idx: int, text: str, conflicts: list[Conflict]
    ) -> tuple[str, int]:
        """使用AI修复章节中的事实矛盾"""
        conflict_descriptions = "\n".join(
            f"- {c.description} (严重度: {c.severity.value})" for c in conflicts
        )

        prompt = (
            f"以下章节存在与前面章节的事实矛盾:\n\n"
            f"{conflict_descriptions}\n\n"
            f"请修复以下章节内容，使事实与前面章节一致。"
            f"仅修改矛盾相关的段落，保持其余内容不变。\n\n"
            f"=== 第{chapter_idx}章 ===\n{text[:4000]}\n\n"
            f"请输出修复后的完整章节:"
        )

        try:
            params = type("Params", (), {
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
                "max_tokens": 6144,
                "model": getattr(self.provider, "model", ""),
                "system": FIXER_SYSTEM,
            })()
            result = self.provider.generate(params)
            changed = abs(len(result.text) - len(text))
            logger.info(f"第{chapter_idx}章修复完成, 变更约{changed}字, ${result.cost:.4f}")
            return (result.text, changed)
        except Exception as e:
            logger.error(f"第{chapter_idx}章修复失败: {e}")
            return (text, 0)

    def verify_only(self, chapter_texts: dict[int, str]) -> list[Conflict]:
        """仅检测冲突，不修复（比 stitch 轻量）"""
        all_conflicts: list[Conflict] = []
        all_triples: list[FactTriple] = []

        for idx, text in sorted(chapter_texts.items()):
            cf = self.extractor.extract(text, idx)
            conflicts, new_triples = self.verifier.verify_batch(cf.triples, all_triples)
            all_triples.extend(new_triples)
            all_conflicts.extend(conflicts)

        return all_conflicts
