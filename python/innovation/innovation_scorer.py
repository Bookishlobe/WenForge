"""创新度评分模型

AI 自动评估每个灵感的创新程度（1-10分），帮助用户快速筛选。
评估维度：题材稀有度、设定独特性、近期市场饱和度、用户个人风格匹配度。
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger("wenforge.innovation.scorer")


class InnovationScorer:
    """创新度评分模型"""

    def __init__(self, provider: Any, model: str):
        self.provider = provider
        self.model = model

    def score(self, idea: dict) -> dict:
        """对单个灵感进行创新度评估，返回评估结果"""
        system = (
            "你是一位资深的中国网文市场分析师和编辑。"
            "你能准确评估一个故事概念的创新程度和市场潜力。"
            "请严格按照JSON格式输出评估结果。"
        )

        prompt = f"""请评估以下网文创意的创新度和市场潜力。

【创意信息】
- 类型: {idea.get('type', '未知')}
- 标题: {idea.get('title', '无')}
- 描述: {idea.get('description', '无')}
- 卖点: {idea.get('hook', '无')}
- 标签: {', '.join(idea.get('tags', []))}
- 类似作品: {', '.join(idea.get('similar_works', []))}

请从以下四个维度进行评分（1-10分）：
1. 题材稀有度：这个创意在市场上的稀缺程度
2. 设定独特性：设定本身的新颖程度
3. 市场饱和度：类似概念在市场上的竞争程度（高分=不饱和）
4. 用户风格匹配度：概念的通用适配度（假设目标用户为网文作者）

输出JSON格式（不要markdown标记）：
{{
  "overall_score": 7,
  "dimensions": {{
    "rarity": 8,
    "uniqueness": 7,
    "market_unsaturated": 6,
    "style_fit": 7
  }},
  "level": "中度创新",
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["劣势1", "劣势2"],
  "suggestion": "改进建议（30字以内）"
}}

评分等级说明：
- 8-10: 高度创新，网文市场少见，有独特差异化卖点
- 5-7: 中度创新，经典套路的有效变体，读者有新鲜感
- 2-4: 常规套路，市场常见模式，竞争激烈
- 1: 过度使用，不建议使用"""

        try:
            response = self._call(system, prompt, temperature=0.3)
            text = response.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            result = json.loads(text)
            result.setdefault("overall_score", 5)
            result.setdefault("level", "中度创新")
            result.setdefault("strengths", [])
            result.setdefault("weaknesses", [])
            result.setdefault("suggestion", "")
            return result
        except Exception as e:
            logger.warning(f"Scoring failed: {e}")
            return self._fallback()

    def batch_score(self, ideas: list[dict]) -> list[dict]:
        """批量评分"""
        results = []
        for idea in ideas:
            try:
                score_result = self.score(idea)
                idea["innovation_score"] = score_result.get("overall_score", 5)
                idea["scoring"] = score_result
                results.append(idea)
            except Exception as e:
                logger.error(f"Batch scoring failed for {idea.get('id', 'unknown')}: {e}")
                idea["innovation_score"] = 5
                idea["scoring"] = self._fallback()
                results.append(idea)
        return results

    def _call(self, system: str, prompt: str, temperature: float = 0.3,
              max_tokens: int = 2048) -> str:
        params = type("Params", (), {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "model": self.model,
            "system": system,
        })()
        return self.provider.generate(params).text

    def _fallback(self) -> dict:
        return {
            "overall_score": 5,
            "dimensions": {
                "rarity": 5, "uniqueness": 5,
                "market_unsaturated": 5, "style_fit": 5,
            },
            "level": "中度创新",
            "strengths": [],
            "weaknesses": ["需要进一步人工评估"],
            "suggestion": "建议结合个人经验判断",
        }
