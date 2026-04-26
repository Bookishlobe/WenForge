"""Tests for fact_engine: extractor, verifier, triple_store."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from fact_engine.models import FactTriple, FactType, Conflict, ConflictSeverity, ChapterFacts
from fact_engine.extractor import FactExtractor
from fact_engine.verifier import FactVerifier
from fact_engine.triple_store import TripleStore


class TestFactTriple:
    def test_key_is_subject_colon_attribute(self):
        t = FactTriple("主角", "修为", "金丹期")
        assert t.key == "主角:修为"

    def test_defaults(self):
        t = FactTriple("张三", "状态", "受伤")
        assert t.chapter == 0
        assert t.confidence == 0.8
        assert t.fact_type == FactType.CHARACTER_STATE


class TestConflict:
    def test_fix_hint_format(self):
        old = FactTriple("主角", "修为", "筑基期", chapter=5, confidence=0.9)
        new = FactTriple("主角", "修为", "金丹期", chapter=10, confidence=0.9)
        conflict = Conflict(
            existing=old, incoming=new,
            severity=ConflictSeverity.WARNING, description="测试冲突",
        )
        hint = conflict.fix_hint
        assert "第5章" in hint
        assert "第10章" in hint
        assert "筑基期" in hint
        assert "金丹期" in hint


class TestChapterFacts:
    def test_default_constructor(self):
        cf = ChapterFacts(chapter_index=3)
        assert cf.chapter_index == 3
        assert cf.triples == []
        assert cf.raw_text == ""
        assert cf.extract_time == 0.0


class TestFactExtractorRuleBased:
    def test_extract_breakthrough(self):
        extractor = FactExtractor()
        cf = extractor.extract("主角突破到金丹期，实力大增。", 1)
        breakthrough = [t for t in cf.triples if t.attribute == "修为"]
        assert len(breakthrough) >= 1
        assert breakthrough[0].subject == "主角"
        assert "金丹" in breakthrough[0].value

    def test_extract_death(self):
        extractor = FactExtractor()
        cf = extractor.extract("张三战死沙场，众人悲痛。", 5)
        deaths = [t for t in cf.triples if "死" in t.subject or t.value == "已死亡"]
        assert len(deaths) >= 1

    def test_extract_master_relationship(self):
        extractor = FactExtractor()
        cf = extractor.extract("叶凡拜药老为师，开始学习炼丹术。", 3)
        rels = [t for t in cf.triples if t.fact_type == FactType.RELATIONSHIP]
        assert len(rels) >= 1
        assert rels[0].attribute == "师徒关系"

    def test_extract_item_acquisition(self):
        extractor = FactExtractor()
        cf = extractor.extract("主角获得了上古神剑，威力无穷。", 2)
        items = [t for t in cf.triples if t.fact_type == FactType.ITEM_OWNERSHIP]
        assert len(items) >= 1

    def test_extract_location(self):
        extractor = FactExtractor()
        cf = extractor.extract("一行人抵达了帝都。", 4)
        locs = [t for t in cf.triples if t.fact_type == FactType.LOCATION]
        assert len(locs) >= 1

    def test_extract_skill_comprehension(self):
        extractor = FactExtractor()
        cf = extractor.extract("主角领悟了剑意，剑法大进。", 6)
        skills = [t for t in cf.triples if t.fact_type == FactType.CAPABILITY]
        assert len(skills) >= 1

    def test_extract_empty_text(self):
        extractor = FactExtractor()
        cf = extractor.extract("", 1)
        assert cf.chapter_index == 1
        assert cf.triples == []

    def test_extract_returns_chapter_facts(self):
        extractor = FactExtractor()
        cf = extractor.extract("主角突破到元婴期。", 7)
        assert isinstance(cf, ChapterFacts)
        assert cf.chapter_index == 7
        assert cf.extract_time >= 0


class TestFactVerifier:
    def test_no_conflict_when_no_matching_key(self):
        verifier = FactVerifier()
        incoming = FactTriple("主角", "修为", "金丹期", chapter=10)
        existing = [FactTriple("配角", "修为", "筑基期", chapter=5)]
        assert verifier.verify(incoming, existing) is None

    def test_no_conflict_when_same_value(self):
        verifier = FactVerifier()
        incoming = FactTriple("主角", "修为", "金丹期", chapter=10)
        existing = [FactTriple("主角", "修为", "金丹期", chapter=5)]
        assert verifier.verify(incoming, existing) is None

    def test_progression_is_info(self):
        verifier = FactVerifier()
        incoming = FactTriple("主角", "修为", "元婴期", chapter=20)
        existing = [FactTriple("主角", "修为", "金丹期", chapter=10)]
        result = verifier.verify(incoming, existing)
        assert result is not None
        assert result.severity == ConflictSeverity.INFO

    def test_regression_is_critical(self):
        verifier = FactVerifier()
        incoming = FactTriple("主角", "修为", "筑基期", chapter=20)
        existing = [FactTriple("主角", "修为", "元婴期", chapter=10, confidence=0.9)]
        result = verifier.verify(incoming, existing)
        assert result is not None
        assert result.severity == ConflictSeverity.CRITICAL

    def test_death_reversal_is_critical(self):
        verifier = FactVerifier()
        incoming = FactTriple("张三", "状态", "存活", chapter=50)
        existing = [FactTriple("张三", "状态", "已死亡", chapter=45, confidence=0.95)]
        result = verifier.verify(incoming, existing)
        assert result is not None
        assert result.severity == ConflictSeverity.CRITICAL

    def test_verify_batch_returns_conflicts_and_new(self):
        verifier = FactVerifier()
        incoming = [
            FactTriple("主角", "修为", "金丹期", chapter=5),
            FactTriple("主角", "武器", "神剑", chapter=5),
        ]
        existing = [FactTriple("主角", "修为", "筑基期", chapter=3)]
        conflicts, new_triples = verifier.verify_batch(incoming, existing)
        assert len(conflicts) == 1
        assert len(new_triples) == 1
        assert new_triples[0].attribute == "武器"


class TestTripleStore:
    def test_save_and_load_chapter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TripleStore(data_dir=Path(tmpdir))
            facts = ChapterFacts(chapter_index=1, triples=[
                FactTriple("主角", "修为", "练气期", chapter=1, confidence=0.9),
                FactTriple("主角", "武器", "铁剑", chapter=1, fact_type=FactType.ITEM_OWNERSHIP),
            ])
            store.save_chapter("test-book", facts)
            loaded = store.load_chapter("test-book", 1)
            assert loaded.chapter_index == 1
            assert len(loaded.triples) == 2
            assert loaded.triples[0].subject == "主角"

    def test_load_nonexistent_chapter_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TripleStore(data_dir=Path(tmpdir))
            cf = store.load_chapter("test-book", 99)
            assert cf.chapter_index == 99
            assert cf.triples == []

    def test_load_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TripleStore(data_dir=Path(tmpdir))
            for i in range(1, 4):
                store.save_chapter("test-book", ChapterFacts(
                    chapter_index=i,
                    triples=[FactTriple("主角", "修为", f"第{i}层", chapter=i)],
                ))
            all_triples = store.load_all("test-book")
            assert len(all_triples) == 3

    def test_query_by_subject(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TripleStore(data_dir=Path(tmpdir))
            store.save_chapter("test-book", ChapterFacts(chapter_index=1, triples=[
                FactTriple("主角", "修为", "金丹期", chapter=1),
                FactTriple("配角", "修为", "筑基期", chapter=1),
            ]))
            results = store.query("test-book", subject="主角")
            assert len(results) == 1
            assert results[0].subject == "主角"

    def test_rebuild_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = TripleStore(data_dir=Path(tmpdir))
            store.save_chapter("test-book", ChapterFacts(chapter_index=1, triples=[
                FactTriple("主角", "修为", "金丹期", chapter=1),
            ]))
            index = store.rebuild_index("test-book")
            assert "主角:修为" in index
            assert len(index["主角:修为"]) == 1
            assert index["主角:修为"][0]["value"] == "金丹期"


class TestFactExtractorAI:
    def test_ai_extract_falls_back_to_rules_on_error(self):
        provider = MagicMock()
        provider.generate.side_effect = Exception("AI unavailable")
        extractor = FactExtractor(provider=provider, model="test-model")
        cf = extractor.extract("主角突破到金丹期。", 1)
        assert len(cf.triples) >= 1

    def test_ai_extract_with_valid_response(self):
        provider = MagicMock()
        provider.generate.return_value = type("Result", (), {
            "text": json.dumps([
                {"subject": "主角", "attribute": "修为", "value": "元婴期",
                 "fact_type": "character_state", "confidence": 0.95}
            ]),
            "token_count": 50,
            "cost": 0.001,
        })()
        extractor = FactExtractor(provider=provider, model="test-model")
        cf = extractor.extract("主角突破到元婴期。", 3)
        assert len(cf.triples) == 1
        assert cf.triples[0].value == "元婴期"
        assert cf.triples[0].confidence == 0.95
