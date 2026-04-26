"""灵感组合编排

将多个灵感组合为统一的故事框架，支持多维度灵感融合。
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger("wenforge.innovation.composer")


class IdeaComposer:
    """灵感组合编排引擎"""

    def __init__(self, provider: Any, model: str):
        self.provider = provider
        self.model = model

    def compose(self, ideas: list[dict], genre: str = "玄幻",
                style: str = "流畅直白") -> dict:
        """将多个灵感组合为一个统一的故事框架"""
        ideas_text = json.dumps(ideas, ensure_ascii=False, indent=2)

        system = (
            "你是一位资深的网文架构师，擅长将多个创意元素融合为一个完整、自洽的故事框架。"
            "请严格按照JSON格式输出。"
        )

        prompt = f"""请将以下多个创意灵感组合为一个统一的故事框架。

【用户题材】{genre}
【用户风格】{style}

【灵感列表】
{ideas_text}

请分析这些灵感之间的协同效应，设计一个融合它们核心要素的统一故事框架。

输出JSON格式（不要markdown标记）：
{{
  "title": "融合故事标题（4-10字）",
  "hook": "一句话核心卖点（30字以内）",
  "world_setting": "世界观设定（200字以内）",
  "prototype": "主角设定（100字以内）",
  "core_conflict": "核心冲突（100字以内）",
  "story_arcs": ["故事弧1（30字）", "故事弧2（30字）", "故事弧3（30字）"],
  "innovation_elements": ["创新点1", "创新点2", "创新点3"],
  "compose_score": 7,
  "note": "组合说明（80字以内，解释各灵感的融合方式）"
}}

compose_score 范围1-10，评估组合后的整体创新度。"""

        try:
            response = self._call(system, prompt, temperature=0.75)
            text = response.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            result = json.loads(text)
            result.setdefault("title", "融合故事")
            result.setdefault("story_arcs", [])
            result.setdefault("innovation_elements", [])
            result.setdefault("compose_score", 5)
            return result
        except Exception as e:
            logger.error(f"Compose failed: {e}")
            return self._fallback()

    def expand(self, idea: dict) -> dict:
        """将单个灵感展开为完整故事大纲"""
        system = (
            "你是一位网文创作专家，擅长将一个核心创意扩展为完整的故事大纲。"
            "请严格按照JSON格式输出。"
        )

        prompt = f"""请将以下创意灵感展开为完整的故事大纲。

【创意信息】
- 类型: {idea.get('type', '未知')}
- 标题: {idea.get('title', '无')}
- 描述: {idea.get('description', '无')}
- 卖点: {idea.get('hook', '无')}
- 标签: {', '.join(idea.get('tags', []))}

输出JSON格式（不要markdown标记）：
{{
  "title": "作品标题（4-10字）",
  "hook": "一句话核心卖点",
  "world_setting": "世界观设定（200字以内）",
  "protagonist": {{
    "name": "主角名",
    "description": "主角设定（50字以内）",
    "motivation": "核心动机"
  }},
  "characters": [
    {{"name": "角色名", "role": "主角/配角/反派", "description": "角色描述（30字）"}}
  ],
  "chapter_outlines": [
    "第1章：内容概要（40字以内）",
    "第2章：内容概要（40字以内）",
    "第3章：内容概要（40字以内）"
  ],
  "story_arcs": "主线故事描述（100字以内）",
  "estimated_chapters": 20,
  "target_audience": "目标读者群体描述"
}}

章节大纲至少生成5章。"""

        try:
            response = self._call(system, prompt, temperature=0.75, max_tokens=4096)
            text = response.strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            result = json.loads(text)
            if isinstance(result.get("chapter_outlines"), list):
                outlines = result["chapter_outlines"]
                if len(outlines) < 5:
                    result["chapter_outlines"] = self._pad_outlines(outlines, 5)
            return result
        except Exception as e:
            logger.error(f"Expand failed: {e}")
            return self._fallback_expand()

    def _call(self, system: str, prompt: str, temperature: float = 0.75,
              max_tokens: int = 4096) -> str:
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
            "title": "融合故事框架",
            "hook": "多个创意元素的融合之作",
            "world_setting": "融合创意世界观",
            "prototype": "待定",
            "core_conflict": "待定",
            "story_arcs": ["主线待定"],
            "innovation_elements": [],
            "compose_score": 5,
            "note": "生成失败，请重试",
        }

    def _fallback_expand(self) -> dict:
        return {
            "title": "创意大纲",
            "hook": "基于创意灵感的展开",
            "world_setting": "待完善的世界观",
            "protagonist": {"name": "待定", "description": "", "motivation": ""},
            "characters": [],
            "chapter_outlines": [
                "第1章：故事开端",
                "第2章：冲突升级",
                "第3章：转折",
                "第4章：高潮",
                "第5章：阶段性结局",
            ],
            "story_arcs": "待完善",
            "estimated_chapters": 20,
            "target_audience": "网文读者",
        }

    def _pad_outlines(self, outlines: list, minimum: int) -> list:
        while len(outlines) < minimum:
            outlines.append(f"第{len(outlines)+1}章：情节继续发展")
        return outlines
