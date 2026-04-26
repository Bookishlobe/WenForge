"""WenForge AI 自动写作引擎

自动生成小说大纲并逐章创作，实现"一键创作"核心体验。
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger("wenforge.auto_writer")

STYLE_DESCRIPTIONS = {
    "流畅直白": "语言简洁明了，节奏明快，适合快速阅读的爽文风格",
    "细腻描写": "注重细节刻画，环境渲染和人物心理描写深入",
    "幽默诙谐": "对话风趣，情节轻松，常有搞笑桥段和反差萌",
    "严肃正剧": "文风偏正式，情节严肃认真，注重逻辑和深度",
    "古风典雅": "运用古风词汇，文笔典雅有韵味",
    "轻松爽文": "节奏爽快不拖沓，主角强势，让读者感到畅快淋漓",
}

CHAPTER_LENGTHS = {
    "short": 2000,
    "medium": 3000,
    "long": 5000,
}


class AutoWriter:
    """AI 自动写作引擎，负责大纲生成和逐章创作。"""

    def __init__(self, provider: Any, model: str):
        self.provider = provider
        self.model = model

    # ── Internal helpers ──────────────────────────────────────

    def _call(self, system: str, prompt: str, temperature: float = 0.7,
              max_tokens: int = 4096) -> str:
        params = type("Params", (), {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "model": self.model,
            "system": system,
        })()
        return self.provider.generate(params).text

    # ── Outline generation ────────────────────────────────────

    def generate_outline(self, config: dict) -> dict:
        """根据用户配置生成完整的小说大纲（世界观、人物、章节大纲）。"""
        genre = config.get("genre", "玄幻")
        premise = config.get("premise", "")
        protagonist = config.get("protagonist", "未命名")
        style = config.get("style", "流畅直白")
        style_desc = STYLE_DESCRIPTIONS.get(style, "")
        chapters = config.get("total_chapters", 10)

        system = (
            "你是起点中文网顶级作家，擅长创作百万字长篇网络小说。\n"
            "你设计的大纲格局宏大，前期铺垫扎实，为超长篇连载留足发展空间。\n"
            "请严格按照 JSON 格式输出，不要包含其他任何内容。"
        )

        prompt = f"""请为我创作一部百万字长篇网络小说的前期大纲。

【题材】{genre}
【核心创意】{premise}
【主角】{protagonist}
【风格】{style} - {style_desc}
【本章节数】{chapters} 章

注意：这是一部计划连载千章以上的百万字长篇网文。
当前需要生成的 {chapters} 章只属于整本书最前期的情节内容，相当于开篇第一个小高潮/第一个副本的篇幅。
整个故事的格局要设计得足够大，为后续千章内容留足发展空间。

请输出以下 JSON 格式（不要带 markdown 标记）：
{{
  "title": "作品名称（4-8 字，有吸引力）",
  "world_setting": "世界观设定（200 字以内，包括力量体系、时代背景、势力分布等）",
  "characters": [
    {{"name": "角色名", "role": "主角/配角/反派", "description": "性格外貌描述 30 字"}}
  ],
  "chapter_outlines": [
    "第 1 章标题：本章概要 40 字",
    "第 2 章标题：本章概要 40 字"
  ],
  "story_arcs": "全书主线规划和主要故事弧光（200 字以内）"
}}

确保：
1. 章节数组必须包含恰好 {chapters} 项
2. 每章标题要吸引人，有网文风格
3. 人物 3-5 个，性格鲜明
4. {chapters} 章只是全书的前期开篇内容，节奏不要太快，要为后续发展留出空间
5. 故事弧光要体现这是百万字长篇，设计清晰的长期成长线和势力格局"""

        response = self._call(system, prompt, temperature=0.75)

        try:
            outline = self._parse_json(response)
        except json.JSONDecodeError:
            logger.warning("JSON 解析失败，使用备用大纲")
            outline = self._fallback_outline(config, chapters)

        # 确保章节数正确
        outlines = outline.get("chapter_outlines", [])
        if len(outlines) != chapters:
            outline["chapter_outlines"] = self._pad_chapters(outlines, chapters)

        return outline

    # ── Chapter generation ────────────────────────────────────

    def generate_chapter(
        self,
        outline: dict,
        index: int,
        chapter_outline: str,
        prev_summaries: list[str],
        config: dict,
    ) -> str:
        """根据大纲生成指定章节的完整内容。"""
        target_length = CHAPTER_LENGTHS.get(config.get("chapter_length", "medium"), 3000)
        style = config.get("style", "流畅直白")
        style_desc = STYLE_DESCRIPTIONS.get(style, "")

        context = ""
        if prev_summaries:
            recent = prev_summaries[-5:]
            context = "之前情节概要：\n" + "\n".join(
                f"· 第{i+1}章：{s[:150]}" for i, s in enumerate(recent)
            )

        system = f"""你是一位专业的中国网络小说作家。
写作风格：{style} - {style_desc}

排版要求：
1. 段落短小精悍，每段 1-3 句，严禁写长段落
2. 句号后必须换行，保持行文清爽
3. 对话独立成段，不要和叙述混在同一段
4. 多使用短句，少用长难句，符合网文快节奏阅读习惯

创作要求：
5. 语言自然流畅，不堆砌辞藻
6. 禁止使用 AI 常用表达：值得注意的是、然而、此外、体现了、综上所述、值得一提的是
7. 对话生动自然，贴合人物性格
8. 长短句结合，节奏感强
9. 章节结尾留有悬念或期待感
10. 全文约 {target_length} 字
11. 第一行输出本章标题，不要其他开场白"""

        characters = json.dumps(outline.get("characters", []), ensure_ascii=False)

        prompt = f"""请根据以下大纲创作第 {index} 章。

【书名】{outline.get("title", "")}
【世界观】{outline.get("world_setting", "")}
【人物】{characters}
【本章概要】{chapter_outline}
{context}

第一行输出本章标题（如「第 {index} 章 风起云涌」），空一行后开始正文。正文段落要短小，句号后换行。"""

        return self._call(system, prompt, temperature=0.8, max_tokens=6144)

    # ── Fallbacks ─────────────────────────────────────────────

    def _parse_json(self, text: str) -> dict:
        """从 LLM 回复中提取 JSON 对象。"""
        text = text.strip()
        # 去掉 markdown 代码块标记
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        return json.loads(text)

    def _fallback_outline(self, config: dict, chapters: int) -> dict:
        title = config.get("premise", "") or f"{config.get('genre', '')}之传奇"
        return {
            "title": title[:20] or "未命名作品",
            "world_setting": f"这是一个{config.get('genre', '玄幻')}的世界，强者为尊，弱肉强食。",
            "characters": [
                {"name": config.get("protagonist", "主角"), "role": "主角",
                 "description": "故事的主人公，意志坚定"},
            ],
            "chapter_outlines": [
                f"第{i+1}章：故事继续发展" for i in range(chapters)
            ],
            "story_arcs": "主角的成长与冒险之旅",
        }

    def _pad_chapters(self, outlines: list, target: int) -> list:
        while len(outlines) < target:
            outlines.append(f"第{len(outlines)+1}章：情节继续发展")
        return outlines[:target]
