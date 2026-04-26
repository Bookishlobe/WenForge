"""流水线编排器 —— 串联规划→拆卡→写作→缝合的完整流程

Pipeline phases:
  BLUEPRINT → STORYBOARDING → DRAFTING → STITCHING → FIXING → STYLE_INJECTION → DONE
"""

from __future__ import annotations

import logging
from typing import Any, Optional, Callable

from .models import ChapterCard, QualityTier, PipelinePhase, PipelineState
from .chapter_card import ChapterCardGenerator
from .batch_writer import BatchWriter
from .stitcher import Stitcher, StitchResult
from fact_engine.triple_store import TripleStore

logger = logging.getLogger("wenforge.pipeline.orchestrator")

ProgressCallback = Callable[[PipelineState], None]


class PipelineOrchestrator:
    """编排从大纲到成稿的完整流水线。"""

    def __init__(
        self,
        provider_a: Any = None,
        provider_b: Any = None,
        provider_c: Any = None,
        stitching_provider: Any = None,
        book_id: str = "",
    ):
        self.state: Optional[PipelineState] = None
        self.card_generator = ChapterCardGenerator()
        self.batch_writer = BatchWriter(provider_a, provider_b, provider_c)
        self.stitcher = Stitcher(
            provider=stitching_provider or provider_a,
            store=TripleStore(),
            book_id=book_id,
        )
        self._on_progress: Optional[ProgressCallback] = None
        self._abort_flag = False

    def on_progress(self, cb: ProgressCallback) -> None:
        self._on_progress = cb

    def abort(self) -> None:
        self._abort_flag = True

    def run(
        self,
        outline: dict,
        total_chapters: int,
        pipeline_id: str = "",
        book_id: str = "",
    ) -> PipelineState:
        """执行完整流水线。

        Args:
            outline: 大纲数据（含 chapter_outlines, characters 等）
            total_chapters: 总章节数
            pipeline_id: 流水线ID
            book_id: 书籍ID
        """
        self._abort_flag = False
        self.stitcher.book_id = book_id

        state = PipelineState(
            pipeline_id=pipeline_id,
            book_id=book_id,
            total_chapters=total_chapters,
        )
        self.state = state

        try:
            # Phase 1: Storyboarding
            self._transition(PipelinePhase.STORYBOARDING)
            cards = self.card_generator.generate(outline, total_chapters)
            if self._abort_flag:
                return state
            self._notify()

            # Phase 2: Drafting
            self._transition(PipelinePhase.DRAFTING)
            results = self.batch_writer.write_batch(cards)
            if self._abort_flag:
                return state

            for idx, (text, cost, tier) in results.items():
                state.chapter_texts[idx] = text
                state.completed_chapters.append(idx)
                state.cost_so_far += cost
            self._notify()

            # Phase 3: Stitching
            self._transition(PipelinePhase.STITCHING)
            fixed_texts, stitch_result = self.stitcher.stitch(
                state.chapter_texts, state
            )
            state.chapter_texts = fixed_texts
            self._notify()

            # Phase 4: Fixing loop (up to 3 rounds)
            if stitch_result.critical:
                self._transition(PipelinePhase.FIXING)
                for round_num in range(3):
                    if self._abort_flag:
                        break
                    fixed_texts, fix_result = self.stitcher.stitch(
                        state.chapter_texts, state
                    )
                    state.chapter_texts = fixed_texts
                    if fix_result.is_clean:
                        logger.info(f"修复第{round_num+1}轮：冲突已解决")
                        break
                self._notify()

            self._transition(PipelinePhase.DONE)
            self._notify()
            logger.info(
                f"流水线完成: {len(state.completed_chapters)}/{total_chapters}章, "
                f"成本${state.cost_so_far:.4f}"
            )
        except Exception as e:
            logger.error(f"流水线执行失败: {e}")
            state.errors.append(str(e))

        return state

    def run_batch(
        self,
        cards: list[ChapterCard],
        pipeline_id: str = "",
        book_id: str = "",
    ) -> PipelineState:
        """从章节卡直接生成（跳过蓝图和拆卡阶段）。"""
        self._abort_flag = False
        self.stitcher.book_id = book_id

        state = PipelineState(
            pipeline_id=pipeline_id,
            book_id=book_id,
            total_chapters=len(cards),
        )
        self.state = state

        try:
            self._transition(PipelinePhase.DRAFTING)
            results = self.batch_writer.write_batch(cards)
            if self._abort_flag:
                return state

            for idx, (text, cost, tier) in results.items():
                state.chapter_texts[idx] = text
                state.completed_chapters.append(idx)
                state.cost_so_far += cost
            self._notify()

            self._transition(PipelinePhase.STITCHING)
            fixed_texts, _ = self.stitcher.stitch(state.chapter_texts, state)
            state.chapter_texts = fixed_texts
            self._notify()

            self._transition(PipelinePhase.DONE)
            self._notify()
        except Exception as e:
            logger.error(f"批量流水线失败: {e}")
            state.errors.append(str(e))

        return state

    def estimate_cost(self, outline: dict, total_chapters: int) -> dict[str, float]:
        """预估流水线成本"""
        cards = self.card_generator.generate(outline, total_chapters)
        card_cost = self.batch_writer.estimate_cost(cards)
        card_cost["stitch_est"] = total_chapters * 1000 * 0.003 / 1000
        card_cost["total_with_stitch"] = card_cost["total_est"] + card_cost["stitch_est"]
        return card_cost

    def _transition(self, phase: PipelinePhase) -> None:
        if self.state:
            self.state.phase = phase
        logger.info(f"流水线阶段: {phase.value}")

    def _notify(self) -> None:
        if self._on_progress and self.state:
            self._on_progress(self.state)
