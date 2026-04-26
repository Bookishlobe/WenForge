"""三元组存储 —— JSON 文件持久化

结构:
  data/facts/{book_id}/
    ├── chapter_0001.json
    ├── chapter_0002.json
    └── _index.json    (全集合索引)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from .models import FactTriple, FactType, ChapterFacts

logger = logging.getLogger("wenforge.fact_engine.store")

DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "facts"


class TripleStore:
    """管理事实三元组的持久化存储。"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def book_dir(self, book_id: str) -> Path:
        d = self.data_dir / book_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_chapter(self, book_id: str, chapter_facts: ChapterFacts) -> Path:
        book = self.book_dir(book_id)
        filename = f"chapter_{chapter_facts.chapter_index:04d}.json"
        path = book / filename

        data = {
            "chapter_index": chapter_facts.chapter_index,
            "triples": [
                {
                    "subject": t.subject,
                    "attribute": t.attribute,
                    "value": t.value,
                    "chapter": t.chapter,
                    "confidence": t.confidence,
                    "source_text": t.source_text,
                    "fact_type": t.fact_type.value,
                }
                for t in chapter_facts.triples
            ],
            "extract_time": chapter_facts.extract_time,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info(f"保存第{chapter_facts.chapter_index}章事实: {path}")
        return path

    def load_chapter(self, book_id: str, chapter_index: int) -> ChapterFacts:
        book = self.book_dir(book_id)
        path = book / f"chapter_{chapter_index:04d}.json"

        if not path.exists():
            return ChapterFacts(chapter_index=chapter_index)

        data = json.loads(path.read_text(encoding="utf-8"))
        triples = [FactTriple(
            subject=t["subject"],
            attribute=t["attribute"],
            value=t["value"],
            chapter=t.get("chapter", chapter_index),
            confidence=t.get("confidence", 0.8),
            source_text=t.get("source_text", ""),
            fact_type=FactType(t.get("fact_type", "character_state")),
        ) for t in data.get("triples", [])]

        return ChapterFacts(
            chapter_index=chapter_index,
            triples=triples,
            extract_time=data.get("extract_time", 0.0),
        )

    def load_all(self, book_id: str, max_chapters: int = 9999) -> list[FactTriple]:
        all_triples: list[FactTriple] = []
        book = self.book_dir(book_id)

        for path in sorted(book.glob("chapter_*.json")):
            chapter_facts = self.load_chapter(book_id, int(path.stem.split("_")[1]))
            all_triples.extend(chapter_facts.triples)
            if len({t.chapter for t in all_triples}) >= max_chapters:
                break

        logger.info(f"加载 {book_id} 全部事实: {len(all_triples)} 条")
        return all_triples

    def query(
        self,
        book_id: str,
        subject: Optional[str] = None,
        fact_type: Optional[str] = None,
    ) -> list[FactTriple]:
        all_triples = self.load_all(book_id)
        results = all_triples
        if subject:
            results = [t for t in results if subject in t.subject]
        if fact_type:
            results = [t for t in results if t.fact_type.value == fact_type]
        return results

    def rebuild_index(self, book_id: str) -> dict[str, list[dict]]:
        all_triples = self.load_all(book_id)
        index: dict[str, list[dict]] = {}
        for t in all_triples:
            if t.key not in index:
                index[t.key] = []
            index[t.key].append({
                "value": t.value,
                "chapter": t.chapter,
                "confidence": t.confidence,
                "fact_type": t.fact_type.value,
            })
        book = self.book_dir(book_id)
        (book / "_index.json").write_text(
            json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return index
