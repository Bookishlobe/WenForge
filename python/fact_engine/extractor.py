"""事实提取器 —— 从网文章节中提取结构化事实三元组

主方案: AI prompt-based 提取（通过已配置的 provider）
降级方案: 基于规则的中文模式匹配（不依赖AI后端）
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from .models import FactTriple, FactType, ChapterFacts

logger = logging.getLogger("wenforge.fact_engine.extractor")


class FactExtractor:
    """从章节文本中提取事实三元组。"""

    def __init__(self, provider: Any = None, model: str = ""):
        self.provider = provider
        self.model = model

    def extract(self, text: str, chapter_index: int) -> ChapterFacts:
        """从章节文本提取所有事实"""
        t0 = time.time()

        triples: list[FactTriple] = []
        if self.provider is not None:
            try:
                triples = self._ai_extract(text, chapter_index)
            except Exception as e:
                logger.warning(f"AI事实提取失败，降级到规则提取: {e}")
                triples = self._rule_extract(text, chapter_index)
        else:
            triples = self._rule_extract(text, chapter_index)

        elapsed = time.time() - t0
        logger.info(
            f"第{chapter_index}章提取 {len(triples)} 条事实, 耗时 {elapsed:.2f}s"
        )
        return ChapterFacts(
            chapter_index=chapter_index,
            triples=triples,
            raw_text=text[:500],
            extract_time=elapsed,
        )

    def _ai_extract(self, text: str, chapter_index: int) -> list[FactTriple]:
        """AI提取事实三元组"""
        text_sample = text[:4000]

        system = (
            "你是一个事实提取器。请从给定的网文章节中提取关键事实。"
            "只提取明确陈述的事实，不要推断。"
            "以 JSON 数组格式输出，每个元素包含: "
            "subject(主体), attribute(属性), value(值), "
            "fact_type(类型: character_state/relationship/item_ownership/location/timeline/capability), "
            "confidence(置信度0-1)。"
            "只输出 JSON，不要其他内容。"
        )

        prompt = f"""从以下网文章节中提取所有明确陈述的关键事实:

{text_sample}

请提取的事实类型包括:
1. character_state: 人物状态（修为等级、受伤/健康、年龄变化等）
2. relationship: 人物关系变化（结为师徒、成为恋人/敌人等）
3. item_ownership: 物品归属（获得/失去/转赠法宝、丹药等）
4. location: 地点变化（到达/离开某地）
5. timeline: 时间标记事件
6. capability: 能力/技能（学会、掌握、突破）

直接输出 JSON 数组，格式如下:
[{{"subject":"主角","attribute":"修为","value":"金丹期","fact_type":"character_state","confidence":0.9}}]"""

        params = type("Params", (), {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 2048,
            "model": self.model,
            "system": system,
        })()

        result = self.provider.generate(params)
        return self._parse_triples(result.text, chapter_index, text)

    def _rule_extract(self, text: str, chapter_index: int) -> list[FactTriple]:
        """基于规则的事实提取（降级方案）"""
        triples: list[FactTriple] = []

        patterns: list[tuple[str, FactType, str]] = [
            (r"(\S{1,8})突破(?:到|至|了)?(\S{1,8})(?:境|期|层)", FactType.CHARACTER_STATE, "修为"),
            (r"(\S{1,8})(?:晋|突)升(?:为)?(\S{1,8})", FactType.CHARACTER_STATE, "修为"),
            (r"(\S{1,8})拜(\S{1,8})为师", FactType.RELATIONSHIP, "师徒关系"),
            (r"(\S{1,8})(?:炼制|得到|获得|入手)了(\S{1,8})", FactType.ITEM_OWNERSHIP, "持有者"),
            (r"(\S{1,8})抵达(?:了)?(\S{1,8})", FactType.LOCATION, "位置"),
            (r"(\S{1,8})领悟(?:了|出)?(\S{1,8})", FactType.CAPABILITY, "技能"),
            (r"(\S{1,8})(?:死|战死|陨落|牺牲)", FactType.CHARACTER_STATE, "状态"),
        ]

        for pattern, fact_type, attr in patterns:
            for match in re.finditer(pattern, text):
                subject = match.group(1)
                value = match.group(2) if match.lastindex and match.lastindex >= 2 else "已死亡"
                triples.append(FactTriple(
                    subject=subject.strip(),
                    attribute=attr,
                    value=value.strip(),
                    chapter=chapter_index,
                    confidence=0.7,
                    source_text=match.group(0)[:200],
                    fact_type=fact_type,
                ))

        logger.info(f"规则提取: 第{chapter_index}章找到 {len(triples)} 条事实")
        return triples

    def _parse_triples(
        self, text: str, chapter_index: int, source: str
    ) -> list[FactTriple]:
        """解析AI返回的三元组JSON"""
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        try:
            raw_list = json.loads(text)
        except json.JSONDecodeError:
            return self._rule_extract(source, chapter_index)

        triples: list[FactTriple] = []
        for item in raw_list:
            try:
                fact_type = FactType(item.get("fact_type", "character_state"))
            except ValueError:
                fact_type = FactType.CHARACTER_STATE

            triples.append(FactTriple(
                subject=item.get("subject", ""),
                attribute=item.get("attribute", ""),
                value=item.get("value", ""),
                chapter=chapter_index,
                confidence=min(max(float(item.get("confidence", 0.8)), 0.0), 1.0),
                source_text=source[:200],
                fact_type=fact_type,
            ))

        return triples
