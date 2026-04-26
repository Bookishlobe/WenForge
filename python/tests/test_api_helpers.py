"""Tests for helper functions in main.py."""

from main import _detect_provider, _get_default_model, _parse_model_route
from config import AppConfig


class TestDetectProvider:
    def test_detect_openai_from_model(self):
        cfg = AppConfig()
        assert _detect_provider("gpt-4o", cfg) == "openai"

    def test_detect_claude_from_model(self):
        cfg = AppConfig()
        assert _detect_provider("claude-sonnet-4-20250514", cfg) == "claude"

    def test_detect_deepseek_from_model(self):
        cfg = AppConfig()
        assert _detect_provider("deepseek-chat", cfg) == "deepseek"

    def test_detect_local_from_model(self):
        cfg = AppConfig()
        assert _detect_provider("qwen2.5:7b", cfg) == "local"

    def test_detect_returns_claude_with_api_key(self):
        cfg = AppConfig()
        cfg.claude.api_key = "sk-ant-test"
        assert _detect_provider("", cfg) == "claude"

    def test_detect_fallback_to_claude(self):
        cfg = AppConfig()
        assert _detect_provider("", cfg) == "claude"


class TestGetDefaultModel:
    def test_openai_default(self):
        cfg = AppConfig()
        assert _get_default_model("openai", cfg) == "gpt-4o-mini"

    def test_claude_default(self):
        cfg = AppConfig()
        assert _get_default_model("claude", cfg) == "gpt-4o-mini"

    def test_deepseek_default(self):
        cfg = AppConfig()
        assert _get_default_model("deepseek", cfg) == "gpt-4o-mini"

    def test_local_default(self):
        cfg = AppConfig()
        assert _get_default_model("local", cfg) == "gpt-4o-mini"


class TestParseModelRoute:
    def test_parse_claude(self):
        provider, model = _parse_model_route("claude-sonnet-4-20250514")
        assert provider == "claude"
        assert model == "claude-sonnet-4-20250514"

    def test_parse_gpt(self):
        provider, model = _parse_model_route("gpt-4o")
        assert provider == "openai"

    def test_parse_deepseek(self):
        provider, model = _parse_model_route("deepseek-chat")
        assert provider == "deepseek"

    def test_parse_local(self):
        provider, model = _parse_model_route("qwen2.5:7b")
        assert provider == "local"
