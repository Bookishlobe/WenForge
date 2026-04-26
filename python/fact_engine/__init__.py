"""WenForge 事实断言引擎

长篇网文的连贯性保障系统。从章节中提取结构化事实三元组，
检测新旧事实之间的冲突，防止百万字级别的"崩坏"。
"""

from .models import FactTriple, Conflict, ConflictSeverity, FactType, ChapterFacts
from .extractor import FactExtractor
from .verifier import FactVerifier
from .triple_store import TripleStore

__all__ = [
    "FactTriple",
    "Conflict",
    "ConflictSeverity",
    "FactType",
    "ChapterFacts",
    "FactExtractor",
    "FactVerifier",
    "TripleStore",
]
