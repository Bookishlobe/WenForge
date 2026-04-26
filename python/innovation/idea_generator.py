"""创新思路库 - 灵感生成引擎

五大创新维度的AI驱动灵感生成器，基于网文市场分析和经典套路解构。
"""

import json
import logging
import re
import uuid
from typing import Any

logger = logging.getLogger("wenforge.innovation")

# ── 各维度生成模板 ──────────────────────────────────────────

IDEA_TYPE_MAP: dict[str, str] = {
    "genre_fusion": "题材融合创新",
    "golden_finger": "金手指创新",
    "world_twist": "世界观反转",
    "character_innovation": "人物设定创新",
    "plot_innovation": "情节结构创新",
}

IDEA_TYPE_DESC: dict[str, str] = {
    "genre_fusion": "将不同题材的核心要素交叉融合，产生全新故事体验",
    "golden_finger": "突破签到/系统等泛滥模式，设计新颖独特的金手指概念",
    "world_twist": "在熟悉设定中完成颠覆性反转，让读者眼前一亮",
    "character_innovation": "非标准主角原型、创新关系组合，避免脸谱化人物",
    "plot_innovation": "非线性叙事、反套路情节链，打破读者预期",
}


# ── 各维度生成器 ────────────────────────────────────────────

class GenreFusionGenerator:
    """题材融合创新生成器"""

    def __init__(self, provider: Any, model: str):
        self.provider = provider
        self.model = model

    def generate(self, genre: str, style: str, keywords: list[str],
                 avoid: list[str], count: int = 3) -> list[dict]:
        system = (
            "你是一位深谙中国网络文学的资深编辑和创意策划师。"
            "擅长将不同题材的核心要素进行创造性融合，设计出既有市场潜力又有独特性的故事概念。"
            "请严格按照JSON格式输出。"
        )

        prompt = f"""请为用户生成 {count} 个【题材融合创新】类的网文灵感概念。

【用户偏好】
- 题材: {genre}
- 风格: {style}
- 关键词: {', '.join(keywords) if keywords else '无'}
- 需避免的套路: {', '.join(avoid) if avoid else '无'}

请将两个或多个不同的题材进行融合（如修真×赛博朋克、悬疑×种田、都市×神话复苏等），
输出符合以下JSON格式的数组（不要markdown标记）：

[
  {{
    "title": "一句话创意标题（8-15字，有吸引力）",
    "description": "详细概念描述（150-200字，说明融合方式、世界观设定、故事基调）",
    "hook": "一句话卖点/钩子（20字以内，能激发读者好奇心）",
    "type": "genre_fusion",
    "innovation_score": 7,
    "market_potential": "高",
    "similar_works": ["类似代表作1", "类似代表作2"],
    "tags": ["标签1", "标签2", "标签3"],
    "avoid_patterns": ["需避开的套路1"]
  }}
]

注意：
1. 融合要自然，不能生硬拼接
2. 优先考虑当前市场较少的融合方向
3. 每个概念要区别于市场上已有的类似作品
4. innovation_score 范围1-10，请给出客观评分
5. market_potential 为"高"/"中"/"低"三档"""

        response = self._call(system, prompt, temperature=0.85)
        return self._parse_list(response, count, "genre_fusion")

    def _call(self, system: str, prompt: str, temperature: float = 0.8,
              max_tokens: int = 4096) -> str:
        params = type("Params", (), {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "model": self.model,
            "system": system,
        })()
        return self.provider.generate(params).text

    def _parse_list(self, text: str, expected: int, idea_type: str) -> list[dict]:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        try:
            items = json.loads(text)
            if isinstance(items, dict) and "ideas" in items:
                items = items["ideas"]
        except json.JSONDecodeError:
            logger.warning(f"JSON parse failed for {idea_type}, using fallback")
            return self._fallback(idea_type)
        if not isinstance(items, list):
            return self._fallback(idea_type)
        for item in items:
            if "id" not in item:
                item["id"] = f"{idea_type}_{uuid.uuid4().hex[:8]}"
            item.setdefault("type", idea_type)
            item.setdefault("source", "ai_generated")
            item.setdefault("innovation_score", 5)
            item.setdefault("market_potential", "中")
            item.setdefault("tags", [])
            item.setdefault("similar_works", [])
            item.setdefault("avoid_patterns", [])
            item.setdefault("hook", "")
            item.setdefault("description", "")
        return items[:expected]

    def _fallback(self, idea_type: str) -> list[dict]:
        return [{
            "id": f"{idea_type}_{uuid.uuid4().hex[:8]}",
            "title": "创意灵感（请重试生成）",
            "description": "AI生成时出现解析错误，请重试。",
            "hook": "重试生成创意",
            "type": idea_type,
            "innovation_score": 5,
            "market_potential": "中",
            "tags": [],
            "similar_works": [],
            "avoid_patterns": [],
            "source": "ai_generated",
        }]


class GoldenFingerGenerator(GenreFusionGenerator):
    """金手指创新生成器（继承复用_parse_list和_call）"""

    def generate(self, genre: str, style: str, keywords: list[str],
                 avoid: list[str], count: int = 3) -> list[dict]:
        system = (
            "你是一位中国网文创作专家，精通各种金手指设定。"
            "你擅长突破签到系统、抽奖、面板等泛滥套路，设计新颖独特的外挂概念。"
            "请严格按照JSON格式输出。"
        )

        prompt = f"""请为用户生成 {count} 个【金手指创新】类的网文灵感概念。

【用户偏好】
- 题材: {genre}
- 风格: {style}
- 关键词: {', '.join(keywords) if keywords else '无'}
- 需避免的套路: {', '.join(avoid) if avoid else '无'}

金手指是网文中主角的特殊能力或优势。请避免签到系统、神豪系统、抽奖系统、面板等已泛滥的模式，
设计真正新颖、有趣且有限制的金手指概念。

输出JSON数组格式（不要markdown标记）：

[
  {{
    "title": "金手指名称（4-10字，有特色）",
    "description": "详细概念描述（150-200字，说明能力机制、限制条件、成长方式）",
    "hook": "一句话卖点（20字以内）",
    "type": "golden_finger",
    "innovation_score": 7,
    "market_potential": "高",
    "similar_works": ["类似作品参考1"],
    "tags": ["标签1", "标签2"],
    "avoid_patterns": ["已泛滥的类似套路"]
  }}
]

注意：
1. 金手指需要有限制，不能无脑无敌
2. 考虑与题材的契合度
3. innovation_score 请客观评分"""

        response = self._call(system, prompt, temperature=0.85)
        return self._parse_list(response, count, "golden_finger")


class WorldTwistGenerator(GenreFusionGenerator):
    """世界观反转生成器"""

    def generate(self, genre: str, style: str, keywords: list[str],
                 avoid: list[str], count: int = 3) -> list[dict]:
        system = (
            "你是一位擅长颠覆性创意的网文设定专家。"
            "你对传统网文世界观了如指掌，擅长在熟悉设定中埋入令人惊艳的反转。"
            "请严格按照JSON格式输出。"
        )

        prompt = f"""请为用户生成 {count} 个【世界观反转】类的网文灵感概念。

【用户偏好】
- 题材: {genre}
- 风格: {style}
- 关键词: {', '.join(keywords) if keywords else '无'}
- 需避免的套路: {', '.join(avoid) if avoid else '无'}

世界观反转是指在看似熟悉的设定中，埋入颠覆性的真相或设定反转。
例如："全员穿越，但主角是唯一留在原世界的人"
"穿越到修仙世界，发现所谓的飞升其实是批量删除账号"
"重生的不是主角，而是整个世界的所有人"

输出JSON数组格式（不要markdown标记）：

[
  {{
    "title": "反转概念标题（8-15字）",
    "description": "详细描述（150-200字，说明表面设定、真正的反转、故事展开方式）",
    "hook": "一句话钩子（20字以内）",
    "type": "world_twist",
    "innovation_score": 8,
    "market_potential": "高",
    "similar_works": ["类似作品名"],
    "tags": ["标签1", "标签2"],
    "avoid_patterns": ["已用烂的反转套路"]
  }}
]"""

        response = self._call(system, prompt, temperature=0.9)
        return self._parse_list(response, count, "world_twist")


class CharacterInnovationGenerator(GenreFusionGenerator):
    """人物设定创新生成器"""

    def generate(self, genre: str, style: str, keywords: list[str],
                 avoid: list[str], count: int = 3) -> list[dict]:
        system = (
            "你是一位资深网文角色设计师，擅长塑造令读者印象深刻的角色。"
            "你深知如何避免脸谱化，创造有深度、有矛盾、有成长空间的创新人物。"
            "请严格按照JSON格式输出。"
        )

        prompt = f"""请为用户生成 {count} 个【人物设定创新】类的网文灵感概念。

【用户偏好】
- 题材: {genre}
- 风格: {style}
- 关键词: {', '.join(keywords) if keywords else '无'}
- 需避免的套路: {', '.join(avoid) if avoid else '无'}

可以是非标准主角原型（如反英雄、另类成长型），也可以是创新的关系组合（如亦敌亦友的宿敌、非典型师徒），
还可以是反派的合理动机（反派源自价值观冲突而非纯粹邪恶）。

输出JSON数组格式（不要markdown标记）：

[
  {{
    "title": "人物概念标题（4-12字）",
    "description": "详细描述（150-200字，包括人物背景、性格特质、成长弧线、关系网络）",
    "hook": "一句话卖点（20字以内）",
    "type": "character_innovation",
    "innovation_score": 7,
    "market_potential": "中",
    "similar_works": ["类似角色参考"],
    "tags": ["标签1", "标签2"],
    "avoid_patterns": ["脸谱化套路"]
  }}
]"""

        response = self._call(system, prompt, temperature=0.85)
        return self._parse_list(response, count, "character_innovation")


class PlotInnovationGenerator(GenreFusionGenerator):
    """情节结构创新生成器"""

    def generate(self, genre: str, style: str, keywords: list[str],
                 avoid: list[str], count: int = 3) -> list[dict]:
        system = (
            "你是一位深谙叙事结构的网文情节专家。"
            "你擅长设计非线性叙事、反套路情节链和令读者欲罢不能的情节架构。"
            "请严格按照JSON格式输出。"
        )

        prompt = f"""请为用户生成 {count} 个【情节结构创新】类的网文灵感概念。

【用户偏好】
- 题材: {genre}
- 风格: {style}
- 关键词: {', '.join(keywords) if keywords else '无'}
- 需避免的套路: {', '.join(avoid) if avoid else '无'}

可以是环形叙事、多线交织、时间循环、读者预期→颠覆的链式反转等创新结构。

输出JSON数组格式（不要markdown标记）：

[
  {{
    "title": "情节结构名称（6-14字）",
    "description": "详细描述（150-200字，包括叙事结构说明、情节节奏设计、读者体验设计）",
    "hook": "一句话钩子（20字以内）",
    "type": "plot_innovation",
    "innovation_score": 7,
    "market_potential": "中",
    "similar_works": ["类似叙事结构的作品"],
    "tags": ["标签1", "标签2"],
    "avoid_patterns": ["平庸的叙事套路"]
  }}
]"""

        response = self._call(system, prompt, temperature=0.85)
        return self._parse_list(response, count, "plot_innovation")


# ── 统一入口 ────────────────────────────────────────────────

GENERATOR_MAP: dict[str, type[GenreFusionGenerator]] = {
    "genre_fusion": GenreFusionGenerator,
    "golden_finger": GoldenFingerGenerator,
    "world_twist": WorldTwistGenerator,
    "character_innovation": CharacterInnovationGenerator,
    "plot_innovation": PlotInnovationGenerator,
}


class IdeaGenerator:
    """灵感生成引擎 - 统一入口"""

    def __init__(self, provider: Any, model: str):
        self.provider = provider
        self.model = model
        self._generators: dict[str, GenreFusionGenerator] = {}
        for key, cls in GENERATOR_MAP.items():
            self._generators[key] = cls(provider, model)

    def generate(self, idea_type: str | None = None, genre: str = "玄幻",
                 style: str = "流畅直白", keywords: list[str] | None = None,
                 avoid_patterns: list[str] | None = None,
                 count: int = 3) -> dict[str, list[dict]]:
        """按维度生成灵感，idea_type=None 则全部维度生成"""
        keywords = keywords or []
        avoid = avoid_patterns or []
        result: dict[str, list[dict]] = {}

        if idea_type and idea_type in self._generators:
            gen = self._generators[idea_type]
            result[idea_type] = gen.generate(genre, style, keywords, avoid, count)
        else:
            for key, gen in self._generators.items():
                try:
                    result[key] = gen.generate(genre, style, keywords, avoid, max(1, count // 2))
                except Exception as e:
                    logger.error(f"{key} generation failed: {e}")
                    result[key] = gen._fallback(key)

        return result
