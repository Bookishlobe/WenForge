"""WenForge 流水线生成器

将写作拆解为类电影制作流程:
  Storyboarding(章节卡) → Parallel Drafting(并行写作) → Stitching(一致性缝合)

核心组件:
  - ChapterCardGenerator: 大纲 → 自包含章节创作指令
  - BatchWriter: 层级化模型调度(A/B/C)并行生成
  - Stitcher: 跨章节事实冲突检测与修复
  - PipelineOrchestrator: 完整流水线编排
"""

from .models import ChapterCard, QualityTier, PipelinePhase, PipelineState
from .chapter_card import ChapterCardGenerator
from .batch_writer import BatchWriter
from .stitcher import Stitcher, StitchResult
from .orchestrator import PipelineOrchestrator

__all__ = [
    "ChapterCard",
    "QualityTier",
    "PipelinePhase",
    "PipelineState",
    "ChapterCardGenerator",
    "BatchWriter",
    "Stitcher",
    "StitchResult",
    "PipelineOrchestrator",
]
