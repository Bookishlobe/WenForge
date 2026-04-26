"""流水线 API 路由 —— /api/pipeline/*"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .models import PipelineState
from .chapter_card import ChapterCardGenerator
from .stitcher import Stitcher
from .orchestrator import PipelineOrchestrator

logger = logging.getLogger("wenforge.pipeline.api")

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class PipelineCardRequest(BaseModel):
    outline: dict = {}
    total_chapters: int = 10


class StitchRequest(BaseModel):
    chapter_texts: dict[int, str] = {}
    book_id: str = ""


class VerifyRequest(BaseModel):
    chapter_texts: dict[int, str] = {}


@router.post("/generate-cards")
async def generate_chapter_cards(req: PipelineCardRequest):
    """从大纲生成章节卡（不写作）"""
    try:
        generator = ChapterCardGenerator()
        cards = generator.generate(req.outline, req.total_chapters)
        return {
            "cards": [
                {
                    "index": c.index,
                    "goal": c.goal,
                    "involved_characters": c.involved_characters,
                    "key_events": c.key_events,
                    "word_budget": c.word_budget,
                    "emotion_curve": c.emotion_curve,
                    "quality_tier": c.quality_tier.value,
                    "tie_to_previous": c.tie_to_previous,
                    "set_up_for_next": c.set_up_for_next,
                }
                for c in cards
            ],
            "total": len(cards),
            "tier_counts": {
                "A": sum(1 for c in cards if c.quality_tier.value == "A"),
                "B": sum(1 for c in cards if c.quality_tier.value == "B"),
                "C": sum(1 for c in cards if c.quality_tier.value == "C"),
            },
        }
    except Exception as e:
        logger.error(f"章节卡生成失败: {e}")
        raise HTTPException(500, f"章节卡生成失败: {str(e)}")


@router.post("/estimate-cost")
async def estimate_pipeline_cost(req: PipelineCardRequest):
    """预估流水线成本"""
    try:
        orchestrator = PipelineOrchestrator()
        cost = orchestrator.estimate_cost(req.outline, req.total_chapters)
        return cost
    except Exception as e:
        logger.error(f"成本估算失败: {e}")
        raise HTTPException(500, f"成本估算失败: {str(e)}")


@router.post("/stitch")
async def stitch_chapters(req: StitchRequest):
    """对已生成的章节执行一致性缝合"""
    try:
        stitcher = Stitcher(book_id=req.book_id)
        state = PipelineState(
            pipeline_id="api-stitch",
            book_id=req.book_id,
            total_chapters=len(req.chapter_texts),
        )
        fixed_texts, result = stitcher.stitch(req.chapter_texts, state)
        return {
            "fixed_texts": fixed_texts,
            "conflicts": [
                {
                    "severity": c.severity.value,
                    "description": c.description,
                    "existing_chapter": c.existing.chapter,
                    "incoming_chapter": c.incoming.chapter,
                }
                for c in result.conflicts
            ],
            "critical_count": len(result.critical),
            "warning_count": len(result.warnings),
            "info_count": len(result.infos),
            "fix_count": result.fix_count,
            "is_clean": result.is_clean,
            "summary": result.summary,
        }
    except Exception as e:
        logger.error(f"缝合失败: {e}")
        raise HTTPException(500, f"缝合失败: {str(e)}")


@router.post("/verify")
async def verify_chapters(req: VerifyRequest):
    """仅检测冲突不修复（轻量版本）"""
    try:
        stitcher = Stitcher()
        conflicts = stitcher.verify_only(req.chapter_texts)
        return {
            "conflicts": [
                {
                    "severity": c.severity.value,
                    "description": c.description,
                    "existing_chapter": c.existing.chapter,
                    "incoming_chapter": c.incoming.chapter,
                }
                for c in conflicts
            ],
            "total_conflicts": len(conflicts),
            "is_clean": len(conflicts) == 0,
        }
    except Exception as e:
        logger.error(f"验证失败: {e}")
        raise HTTPException(500, f"验证失败: {str(e)}")
