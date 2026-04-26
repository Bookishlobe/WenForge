"""事实断言引擎 API 路由 —— /api/fact/*"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel

from .models import FactTriple, FactType, ConflictSeverity, ChapterFacts
from .extractor import FactExtractor
from .verifier import FactVerifier
from .triple_store import TripleStore

logger = logging.getLogger("wenforge.fact_engine.api")

router = APIRouter(prefix="/api/fact", tags=["fact-engine"])


class ExtractRequest(BaseModel):
    text: str
    chapter_index: int = 1


class VerifyRequest(BaseModel):
    incoming_triples: list[dict] = []
    existing_triples: list[dict] = []


class TripleQueryRequest(BaseModel):
    book_id: str
    subject: str = ""
    fact_type: str = ""


def _triple_from_dict(d: dict, chapter: int = 0) -> FactTriple:
    try:
        ft = FactType(d.get("fact_type", "character_state"))
    except ValueError:
        ft = FactType.CHARACTER_STATE
    return FactTriple(
        subject=d.get("subject", ""),
        attribute=d.get("attribute", ""),
        value=d.get("value", ""),
        chapter=d.get("chapter", chapter),
        confidence=min(max(float(d.get("confidence", 0.8)), 0.0), 1.0),
        source_text=d.get("source_text", ""),
        fact_type=ft,
    )


def _triple_to_dict(t: FactTriple) -> dict:
    return {
        "subject": t.subject,
        "attribute": t.attribute,
        "value": t.value,
        "chapter": t.chapter,
        "confidence": t.confidence,
        "source_text": t.source_text,
        "fact_type": t.fact_type.value,
    }


@router.post("/extract")
async def extract_facts(req: ExtractRequest):
    """从章节文本提取事实三元组"""
    try:
        extractor = FactExtractor()
        chapter_facts = extractor.extract(req.text, req.chapter_index)
        return {
            "chapter_index": chapter_facts.chapter_index,
            "triples": [_triple_to_dict(t) for t in chapter_facts.triples],
            "total": len(chapter_facts.triples),
            "extract_time": chapter_facts.extract_time,
        }
    except Exception as e:
        logger.error(f"事实提取失败: {e}")
        raise HTTPException(500, f"事实提取失败: {str(e)}")


@router.post("/verify")
async def verify_facts(req: VerifyRequest):
    """验证输入事实是否与已有事实冲突"""
    try:
        incoming = [_triple_from_dict(d) for d in req.incoming_triples]
        existing = [_triple_from_dict(d) for d in req.existing_triples]
        verifier = FactVerifier()
        conflicts, new_triples = verifier.verify_batch(incoming, existing)
        return {
            "conflicts": [
                {
                    "severity": c.severity.value,
                    "description": c.description,
                    "fix_hint": c.fix_hint,
                    "existing": _triple_to_dict(c.existing),
                    "incoming": _triple_to_dict(c.incoming),
                }
                for c in conflicts
            ],
            "new_triples": [_triple_to_dict(t) for t in new_triples],
            "conflict_count": len(conflicts),
            "critical_count": sum(1 for c in conflicts if c.severity == ConflictSeverity.CRITICAL),
            "is_clean": len(conflicts) == 0,
        }
    except Exception as e:
        logger.error(f"事实验证失败: {e}")
        raise HTTPException(500, f"事实验证失败: {str(e)}")


@router.post("/store/save")
async def save_chapter_facts(
    book_id: str = Body(...),
    chapter_index: int = Body(...),
    triples: list[dict] = Body(default_factory=list),
):
    """保存某章的事实到存储"""
    try:
        store = TripleStore()
        facts = ChapterFacts(
            chapter_index=chapter_index,
            triples=[_triple_from_dict(d, chapter_index) for d in triples],
        )
        path = store.save_chapter(book_id, facts)
        return {"ok": True, "path": str(path), "count": len(triples)}
    except Exception as e:
        logger.error(f"保存事实失败: {e}")
        raise HTTPException(500, f"保存失败: {str(e)}")


@router.get("/store/load")
async def load_chapter_facts(
    book_id: str = Query(...),
    chapter_index: int = Query(...),
):
    """加载某章的事实"""
    try:
        store = TripleStore()
        cf = store.load_chapter(book_id, chapter_index)
        return {
            "chapter_index": cf.chapter_index,
            "triples": [_triple_to_dict(t) for t in cf.triples],
            "total": len(cf.triples),
        }
    except Exception as e:
        logger.error(f"加载事实失败: {e}")
        raise HTTPException(500, f"加载失败: {str(e)}")


@router.get("/store/all")
async def load_all_facts(
    book_id: str = Query(...),
    max_chapters: int = Query(9999),
):
    """加载书籍的所有事实"""
    try:
        store = TripleStore()
        triples = store.load_all(book_id, max_chapters)
        return {"book_id": book_id, "triples": [_triple_to_dict(t) for t in triples], "total": len(triples)}
    except Exception as e:
        logger.error(f"加载全部事实失败: {e}")
        raise HTTPException(500, f"加载失败: {str(e)}")


@router.post("/store/query")
async def query_facts(req: TripleQueryRequest):
    """按条件查询事实"""
    try:
        store = TripleStore()
        triples = store.query(
            book_id=req.book_id,
            subject=req.subject or None,
            fact_type=req.fact_type or None,
        )
        return {"triples": [_triple_to_dict(t) for t in triples], "total": len(triples)}
    except Exception as e:
        logger.error(f"查询事实失败: {e}")
        raise HTTPException(500, f"查询失败: {str(e)}")


@router.post("/store/rebuild-index")
async def rebuild_index(book_id: str = Body(..., embed=True)):
    """重建书籍的事实索引"""
    try:
        store = TripleStore()
        index = store.rebuild_index(book_id)
        return {"ok": True, "keys": len(index)}
    except Exception as e:
        logger.error(f"重建索引失败: {e}")
        raise HTTPException(500, f"重建索引失败: {str(e)}")
