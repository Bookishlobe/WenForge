"""Tests for pipeline: chapter_card, batch_writer, stitcher, orchestrator."""

from unittest.mock import MagicMock

import pytest

from pipeline.models import ChapterCard, QualityTier, PipelinePhase, PipelineState
from pipeline.chapter_card import ChapterCardGenerator
from pipeline.batch_writer import BatchWriter
from pipeline.stitcher import Stitcher, StitchResult
from pipeline.orchestrator import PipelineOrchestrator


class TestChapterCard:
    def test_to_prompt_includes_goal(self):
        card = ChapterCard(index=1, goal="主角踏上修炼之路")
        prompt = card.to_prompt()
        assert "主角踏上修炼之路" in prompt
        assert "【本章目标】" in prompt

    def test_to_prompt_includes_characters(self):
        card = ChapterCard(index=2, goal="测试", involved_characters=["主角", "师父"])
        prompt = card.to_prompt()
        assert "主角" in prompt
        assert "师父" in prompt
        assert "【涉及人物】" in prompt

    def test_to_prompt_includes_key_events(self):
        card = ChapterCard(index=3, goal="测试", key_events=["修炼", "突破"])
        prompt = card.to_prompt()
        assert "修炼 → 突破" in prompt

    def test_to_prompt_includes_emotion_curve(self):
        card = ChapterCard(index=4, goal="测试", emotion_curve="紧张→释放")
        prompt = card.to_prompt()
        assert "紧张→释放" in prompt

    def test_to_prompt_includes_ties(self):
        card = ChapterCard(
            index=5, goal="测试",
            tie_to_previous="承前章: 主角受伤",
            set_up_for_next="启后章: 主角康复",
        )
        prompt = card.to_prompt()
        assert "承前章" in prompt
        assert "启后章" in prompt

    def test_default_word_budget(self):
        card = ChapterCard(index=1, goal="测试")
        assert card.word_budget == 3000

    def test_default_quality_tier(self):
        card = ChapterCard(index=1, goal="测试")
        assert card.quality_tier == QualityTier.B


class TestChapterCardGenerator:
    def test_generate_first_chapter_is_tier_a(self, sample_outline):
        gen = ChapterCardGenerator()
        cards = gen.generate(sample_outline, 5)
        assert cards[0].quality_tier == QualityTier.A

    def test_generate_last_chapter_is_tier_a(self, sample_outline):
        gen = ChapterCardGenerator()
        cards = gen.generate(sample_outline, 5)
        assert cards[-1].quality_tier == QualityTier.A

    def test_generate_climax_keyword_is_tier_a(self):
        gen = ChapterCardGenerator()
        outline = {
            "chapter_outlines": ["第1章：开篇", "第2章：日常", "第3章：主角突破高潮"],
            "characters": [{"name": "主角"}],
        }
        cards = gen.generate(outline, 3)
        assert cards[2].quality_tier == QualityTier.A

    def test_generate_filler_keyword_is_tier_c(self):
        gen = ChapterCardGenerator()
        outline = {
            "chapter_outlines": ["第1章：开篇", "第2章：主角闭关修炼", "第3章：日常", "第4章：收尾"],
            "characters": [{"name": "主角"}],
        }
        cards = gen.generate(outline, 4)
        assert cards[1].quality_tier == QualityTier.C

    def test_generate_returns_correct_count(self, sample_outline):
        gen = ChapterCardGenerator()
        cards = gen.generate(sample_outline, 7)
        assert len(cards) == 7

    def test_generate_index_starts_at_1(self, sample_outline):
        gen = ChapterCardGenerator()
        cards = gen.generate(sample_outline, 3)
        assert cards[0].index == 1
        assert cards[-1].index == 3

    def test_generate_ties_first_chapter_empty(self, sample_outline):
        gen = ChapterCardGenerator()
        cards = gen.generate(sample_outline, 3)
        assert cards[0].tie_to_previous == ""

    def test_generate_ties_non_first_chapter(self, sample_outline):
        gen = ChapterCardGenerator()
        cards = gen.generate(sample_outline, 3)
        assert cards[1].tie_to_previous != ""

    def test_generate_empty_outline(self):
        gen = ChapterCardGenerator()
        outline = {"chapter_outlines": [], "characters": []}
        cards = gen.generate(outline, 3)
        assert len(cards) == 3
        assert all(c.goal == "情节继续发展" for c in cards)


class TestBatchWriter:
    def test_write_chapter_uses_correct_tier(self, mock_provider):
        writer = BatchWriter(provider_a=mock_provider, provider_b=mock_provider)
        card = ChapterCard(index=1, goal="测试", quality_tier=QualityTier.A)
        text, cost = writer.write_chapter(card)
        assert len(text) > 0
        assert cost > 0

    def test_write_chapter_no_provider_fallback(self):
        writer = BatchWriter()
        card = ChapterCard(index=5, goal="测试目标", quality_tier=QualityTier.B)
        text, cost = writer.write_chapter(card)
        assert "第5章" in text
        assert cost == 0.0

    def test_write_batch_returns_all_indices(self, mock_provider):
        writer = BatchWriter(provider_a=mock_provider, provider_b=mock_provider)
        cards = [
            ChapterCard(index=1, goal="a", quality_tier=QualityTier.A),
            ChapterCard(index=2, goal="b", quality_tier=QualityTier.B),
            ChapterCard(index=3, goal="c", quality_tier=QualityTier.C),
        ]
        results = writer.write_batch(cards)
        assert set(results.keys()) == {1, 2, 3}
        for text, cost, tier in results.values():
            assert isinstance(text, str)
            assert isinstance(cost, float)

    def test_estimate_cost_chapter_counts(self):
        writer = BatchWriter()
        cards = [
            ChapterCard(index=1, goal="a", quality_tier=QualityTier.A),
            ChapterCard(index=2, goal="b", quality_tier=QualityTier.A),
            ChapterCard(index=3, goal="c", quality_tier=QualityTier.B),
            ChapterCard(index=4, goal="d", quality_tier=QualityTier.C),
        ]
        est = writer.estimate_cost(cards)
        assert est["A_chapters"] == 2
        assert est["B_chapters"] == 1
        assert est["C_chapters"] == 1
        assert est["est_cost_c"] == 0.0


class TestPipelineState:
    def test_progress_zero_when_no_chapters(self):
        state = PipelineState(pipeline_id="test", total_chapters=0)
        assert state.progress == 0.0

    def test_progress_half_complete(self):
        state = PipelineState(
            pipeline_id="test", total_chapters=10,
            completed_chapters=[1, 2, 3, 4, 5],
        )
        assert state.progress == 0.5

    def test_progress_full(self):
        state = PipelineState(
            pipeline_id="test", total_chapters=5,
            completed_chapters=[1, 2, 3, 4, 5],
        )
        assert state.progress == 1.0


class TestStitchResult:
    def test_is_clean_when_empty(self):
        result = StitchResult()
        assert result.is_clean

    def test_not_clean_with_warning(self):
        from fact_engine.models import Conflict, ConflictSeverity, FactTriple
        result = StitchResult()
        t = FactTriple("x", "y", "z", chapter=1)
        result.warnings.append(Conflict(
            existing=t, incoming=t, severity=ConflictSeverity.WARNING, description="",
        ))
        assert not result.is_clean

    def test_summary_format(self):
        result = StitchResult()
        assert "缝合完成" in result.summary


class TestStitcher:
    def test_verify_only_no_conflicts_for_empty(self):
        stitcher = Stitcher()
        conflicts = stitcher.verify_only({})
        assert conflicts == []

    def test_verify_only_single_chapter(self):
        stitcher = Stitcher()
        conflicts = stitcher.verify_only({1: "主角突破到金丹期。"})
        assert isinstance(conflicts, list)

    def test_verify_only_two_chapters(self):
        stitcher = Stitcher()
        texts = {1: "主角突破到筑基期。", 2: "主角突破到金丹期。"}
        conflicts = stitcher.verify_only(texts)
        assert isinstance(conflicts, list)


class TestPipelineOrchestrator:
    def test_estimate_cost_returns_expected_keys(self, sample_outline):
        orch = PipelineOrchestrator()
        est = orch.estimate_cost(sample_outline, 5)
        for key in ("A_chapters", "B_chapters", "C_chapters", "total_est", "stitch_est", "total_with_stitch"):
            assert key in est

    def test_run_batch_with_mock_providers(self):
        provider = MagicMock()
        provider.generate.return_value = type("Result", (), {
            "text": "第1章内容...", "token_count": 100, "cost": 0.001, "model": "test",
        })()
        orch = PipelineOrchestrator(provider_a=provider, provider_b=provider)
        cards = [ChapterCard(index=1, goal="测试章节", quality_tier=QualityTier.A)]
        state = orch.run_batch(cards, pipeline_id="test-run", book_id="test-book")
        assert state.total_chapters == 1
        assert len(state.completed_chapters) == 1
        assert state.phase == PipelinePhase.DONE

    def test_run_with_mock_providers(self, sample_outline):
        provider = MagicMock()
        provider.generate.return_value = type("Result", (), {
            "text": "章节内容...", "token_count": 100, "cost": 0.001, "model": "test",
        })()
        orch = PipelineOrchestrator(provider_a=provider, provider_b=provider)
        state = orch.run(sample_outline, total_chapters=2, pipeline_id="test-run", book_id="test-book")
        assert state.total_chapters == 2
        assert len(state.completed_chapters) == 2
        assert state.phase == PipelinePhase.DONE

    def test_abort_flag_stops_early(self, sample_outline):
        """Abort flag is set and run returns early."""
        orch = PipelineOrchestrator()
        orch.abort()
        assert orch._abort_flag is True
        state = orch.run(sample_outline, total_chapters=2)
        assert state.total_chapters == 2

    def test_on_progress_callback(self, sample_outline):
        provider = MagicMock()
        provider.generate.return_value = type("Result", (), {
            "text": "内容", "token_count": 10, "cost": 0.0, "model": "test",
        })()
        orch = PipelineOrchestrator(provider_a=provider, provider_b=provider)
        progress_states = []
        orch.on_progress(lambda s: progress_states.append(s.phase))
        orch.run(sample_outline, total_chapters=1, book_id="test")
        assert len(progress_states) > 0
        assert progress_states[-1] == PipelinePhase.DONE
