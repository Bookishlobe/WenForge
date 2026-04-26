"""事实断言引擎核心数据模型

Fact Triple 是网文世界中一条可验证的事实断言。
用于长篇小说的连贯性检测——当第300章说主角是金丹期时，
系统自动对比第10章的事实记录，发现修为倒退的矛盾。
"""

from __future__ import annotations

from enum import Enum
from typing import Literal
from dataclasses import dataclass, field


class ConflictSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class FactType(str, Enum):
    CHARACTER_STATE = "character_state"
    RELATIONSHIP = "relationship"
    ITEM_OWNERSHIP = "item_ownership"
    LOCATION = "location"
    TIMELINE = "timeline"
    CAPABILITY = "capability"


@dataclass(frozen=True)
class FactTriple:
    """网文世界中的一条可验证事实。

    示例:
        FactTriple("主角", "修为", "金丹期", chapter=10)
        FactTriple("张三", "状态", "已死亡", chapter=45, confidence=0.95)
        FactTriple("神剑", "持有者", "主角", chapter=50)
    """

    subject: str
    attribute: str
    value: str
    chapter: int = 0
    confidence: float = 0.8
    source_text: str = ""
    fact_type: FactType = FactType.CHARACTER_STATE

    @property
    def key(self) -> str:
        return f"{self.subject}:{self.attribute}"


@dataclass(frozen=True)
class Conflict:
    """两个事实之间的冲突"""
    existing: FactTriple
    incoming: FactTriple
    severity: ConflictSeverity
    description: str

    @property
    def fix_hint(self) -> str:
        return (
            f"第{self.existing.chapter}章: {self.existing.subject} 的 "
            f"{self.existing.attribute} = {self.existing.value}\n"
            f"第{self.incoming.chapter}章: {self.incoming.subject} 的 "
            f"{self.incoming.attribute} = {self.incoming.value}\n"
            f"冲突: {self.description}"
        )


@dataclass
class ChapterFacts:
    """某一章提取的所有事实"""
    chapter_index: int
    triples: list[FactTriple] = field(default_factory=list)
    raw_text: str = ""
    extract_time: float = 0.0
