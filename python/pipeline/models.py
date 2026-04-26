"""流水线生成器核心数据模型"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field


class PipelinePhase(str, Enum):
    BLUEPRINT = "blueprint"
    STORYBOARDING = "storyboarding"
    DRAFTING = "drafting"
    STITCHING = "stitching"
    FIXING = "fixing"
    STYLE_INJECTION = "style_injection"
    DONE = "done"


class QualityTier(str, Enum):
    A = "A"  # 旗舰模型 - 核心章节
    B = "B"  # 经济模型 - 推进章节
    C = "C"  # 本地模型 - 填充章节


@dataclass
class ChapterCard:
    """完全自包含的章节创作指令"""
    index: int
    goal: str = ""
    involved_characters: list[str] = field(default_factory=list)
    character_states: dict[str, str] = field(default_factory=dict)
    key_events: list[str] = field(default_factory=list)
    location: str = ""
    word_budget: int = 3000
    emotion_curve: str = ""
    tie_to_previous: str = ""
    set_up_for_next: str = ""
    quality_tier: QualityTier = QualityTier.B

    def to_prompt(self) -> str:
        parts: list[str] = []
        if self.goal:
            parts.append(f"【本章目标】{self.goal}")
        if self.involved_characters:
            parts.append(f"【涉及人物】{', '.join(self.involved_characters)}")
        if self.character_states:
            states = ", ".join(f"{k}={v}" for k, v in self.character_states.items())
            parts.append(f"【人物状态】{states}")
        if self.key_events:
            parts.append(f"【关键事件】{' → '.join(self.key_events)}")
        if self.location:
            parts.append(f"【场景】{self.location}")
        if self.emotion_curve:
            parts.append(f"【情绪曲线】{self.emotion_curve}")
        if self.tie_to_previous:
            parts.append(f"【前情衔接】{self.tie_to_previous}")
        if self.set_up_for_next:
            parts.append(f"【为后章铺垫】{self.set_up_for_next}")
        parts.append(f"【字数】约{self.word_budget}字")
        return "\n".join(parts)


@dataclass
class PipelineState:
    """流水线运行状态"""
    pipeline_id: str
    book_id: str = ""
    phase: PipelinePhase = PipelinePhase.BLUEPRINT
    total_chapters: int = 0
    completed_chapters: list[int] = field(default_factory=list)
    failed_chapters: list[int] = field(default_factory=list)
    chapter_texts: dict[int, str] = field(default_factory=dict)
    cost_so_far: float = 0.0
    errors: list[str] = field(default_factory=list)

    @property
    def progress(self) -> float:
        if self.total_chapters == 0:
            return 0.0
        return len(self.completed_chapters) / self.total_chapters
