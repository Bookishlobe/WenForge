"""章节卡生成器 —— 将大纲拆解为自包含的章节创作指令"""

from __future__ import annotations

import logging

from .models import ChapterCard, QualityTier

logger = logging.getLogger("wenforge.pipeline.chapter_card")


class ChapterCardGenerator:
    """从小说大纲生成章节卡列表。"""

    def generate(self, outline: dict, total_chapters: int) -> list[ChapterCard]:
        chapter_outlines = outline.get("chapter_outlines", [])
        characters = outline.get("characters", [])
        character_names = [c.get("name", "") for c in characters if isinstance(c, dict)]

        cards: list[ChapterCard] = []
        for i in range(total_chapters):
            raw = chapter_outlines[i] if i < len(chapter_outlines) else ""
            title, summary = self._parse_outline_entry(raw, i)
            tier = self._infer_quality_tier(i, total_chapters, summary)

            cards.append(ChapterCard(
                index=i + 1,
                goal=summary,
                involved_characters=self._pick_characters(character_names, summary, i),
                key_events=self._extract_events(summary),
                word_budget=3000,
                emotion_curve=self._infer_emotion(tier),
                tie_to_previous=self._tie_to_previous(i, chapter_outlines),
                set_up_for_next=self._set_up_next(i, total_chapters, chapter_outlines),
                quality_tier=tier,
            ))

        tier_counts = {t: sum(1 for c in cards if c.quality_tier == t) for t in QualityTier}
        logger.info(f"生成 {len(cards)} 张章节卡: A={tier_counts.get(QualityTier.A,0)} B={tier_counts.get(QualityTier.B,0)} C={tier_counts.get(QualityTier.C,0)}")
        return cards

    def _parse_outline_entry(self, raw: str, index: int) -> tuple[str, str]:
        raw = raw.strip()
        if not raw:
            return (f"第{index+1}章", "情节继续发展")
        for sep in ("：", ":"):
            if sep in raw:
                parts = raw.split(sep, 1)
                return (parts[0].strip(), parts[1].strip())
        return (raw[:20], raw)

    def _infer_quality_tier(self, index: int, total: int, summary: str) -> QualityTier:
        is_first = index == 0
        is_last = index == total - 1
        is_quarter = total > 4 and index % max(total // 4, 1) == 0
        if is_first or is_last or is_quarter:
            return QualityTier.A

        climax_kw = ["高潮", "突破", "决战", "死亡", "真相", "反转", "揭秘", "暴走"]
        if any(k in summary for k in climax_kw):
            return QualityTier.A

        filler_kw = ["修炼", "赶路", "炼丹", "闭关", "日常", "收集", "采购"]
        if any(k in summary for k in filler_kw):
            return QualityTier.C

        return QualityTier.B

    def _pick_characters(self, names: list[str], summary: str, index: int) -> list[str]:
        appearing = [n for n in names if n in summary]
        if not appearing:
            appearing = names[:3]
        return appearing[:5]

    def _extract_events(self, summary: str) -> list[str]:
        events = [e.strip() for e in summary.replace("；", ";").replace("、", ";").split(";") if e.strip()]
        return events[:3] if events else [summary[:40]]

    def _infer_emotion(self, tier: QualityTier) -> str:
        return {
            QualityTier.A: "紧张→释放→震撼",
            QualityTier.B: "平稳→小高潮→期待",
            QualityTier.C: "轻松→成长→积累",
        }.get(tier, "平稳推进")

    def _tie_to_previous(self, index: int, outlines: list[str]) -> str:
        if index == 0:
            return ""
        prev = outlines[index - 1] if index - 1 < len(outlines) else ""
        return f"承前章: {prev[:60]}" if prev else ""

    def _set_up_next(self, index: int, total: int, outlines: list[str]) -> str:
        if index >= total - 1:
            return ""
        n = outlines[index + 1] if index + 1 < len(outlines) else ""
        return f"启后章: {n[:60]}" if n else ""
