"""Shared fixtures for WenForge Python tests."""

from typing import Any
from unittest.mock import MagicMock

import pytest


class MockGenerateResult:
    """Simulates a provider generation result."""

    def __init__(self, text: str = "生成的内容", token_count: int = 100,
                 cost: float = 0.001, model: str = "mock-model"):
        self.text = text
        self.token_count = token_count
        self.cost = cost
        self.model = model


@pytest.fixture
def mock_provider():
    """Returns a MagicMock that simulates a working AI provider."""
    provider = MagicMock()
    provider.generate.return_value = MockGenerateResult()
    return provider


@pytest.fixture
def mock_config(monkeypatch):
    """Provides a clean AppConfig with default values."""
    from config import AppConfig
    config = AppConfig()
    monkeypatch.setattr("config._config", config)
    return config


@pytest.fixture
def sample_outline() -> dict[str, Any]:
    """A minimal valid story outline."""
    return {
        "title": "测试小说",
        "world_setting": "这是一个修仙世界",
        "characters": [
            {"name": "主角", "role": "主角", "description": "主人公"},
            {"name": "配角", "role": "配角", "description": "好朋友"},
        ],
        "chapter_outlines": [
            "第1章：主角开始修行",
            "第2章：主角遇险",
        ],
        "story_arcs": "主角的成长之路",
    }


@pytest.fixture
def innovation_idea() -> dict[str, Any]:
    """A sample innovation idea for testing."""
    return {
        "id": "test_001",
        "type": "genre_fusion",
        "title": "修仙赛博朋克",
        "description": "在赛博朋克世界中修仙",
        "hook": "当芯片植入遇上丹田修炼",
        "innovation_score": 8,
        "market_potential": "高",
        "similar_works": [],
        "tags": ["修仙", "赛博朋克"],
        "avoid_patterns": [],
        "source": "ai_generated",
    }
