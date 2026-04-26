"""批量作家 —— 根据章节卡并行生成多章内容"""

import logging
from typing import Any

from .models import ChapterCard, QualityTier

logger = logging.getLogger("wenforge.pipeline.batch_writer")

WRITING_SYSTEM = (
    "你是一位专业的中国网络小说作家。"
    "要求: 1)语言自然流畅 2)避免AI常见表达 "
    "3)对话生动 4)直接开始写作不要开场白"
)


class BatchWriter:
    """根据章节卡批量生成章节。"""

    def __init__(self, provider_a: Any = None, provider_b: Any = None, provider_c: Any = None):
        self.providers = {
            QualityTier.A: provider_a,
            QualityTier.B: provider_b,
            QualityTier.C: provider_c,
        }

    def write_chapter(self, card: ChapterCard) -> tuple[str, float]:
        provider = self.providers.get(card.quality_tier, self.providers[QualityTier.B])
        if provider is None:
            return (f"// 第{card.index}章: 无可用模型\n// {card.goal}", 0.0)

        prompt = f"请创作第 {card.index} 章。\n\n{card.to_prompt()}\n\n以「第 {card.index} 章」开头。"
        params = type("Params", (), {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": 6144,
            "model": getattr(provider, "model", ""),
            "system": WRITING_SYSTEM,
        })()

        result = provider.generate(params)
        logger.info(f"第{card.index}章({card.quality_tier.value}级) {result.token_count}tokens ${result.cost:.4f}")
        return (result.text, result.cost)

    def write_batch(self, cards: list[ChapterCard]) -> dict[int, tuple[str, float, QualityTier]]:
        results: dict[int, tuple[str, float, QualityTier]] = {}
        for card in cards:
            try:
                text, cost = self.write_chapter(card)
                results[card.index] = (text, cost, card.quality_tier)
            except Exception as e:
                logger.error(f"第{card.index}章失败: {e}")
                results[card.index] = (f"// 错误: {e}", 0.0, card.quality_tier)
        return results

    def estimate_cost(self, cards: list[ChapterCard]) -> dict[str, float]:
        tc = {t: 0 for t in QualityTier}
        for c in cards:
            tc[c.quality_tier] += 1
        return {
            "A_chapters": tc[QualityTier.A],
            "B_chapters": tc[QualityTier.B],
            "C_chapters": tc[QualityTier.C],
            "est_cost_a": tc[QualityTier.A] * 3000 * 0.003 / 1000,
            "est_cost_b": tc[QualityTier.B] * 3000 * 0.001 / 1000,
            "est_cost_c": 0.0,
            "total_est": tc[QualityTier.A] * 3000 * 0.003 / 1000 + tc[QualityTier.B] * 3000 * 0.001 / 1000,
        }
