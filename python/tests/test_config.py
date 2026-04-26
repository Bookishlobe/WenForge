"""Tests for config module."""

from config import get_config, update_config, AppConfig


class TestAppConfig:
    def test_default_config(self):
        cfg = AppConfig()
        assert cfg.openai.model == "gpt-4o-mini"
        assert cfg.claude.endpoint is None
        assert cfg.deepseek.endpoint == "https://api.deepseek.com"
        assert cfg.local.endpoint == "http://localhost:11434"

    def test_writing_model_default(self):
        cfg = AppConfig()
        assert cfg.writing_model == "claude-haiku-3-5-20251022"

    def test_polishing_model_default(self):
        cfg = AppConfig()
        assert cfg.polishing_model == "claude-opus-4-20250514"


class TestGetConfig:
    def test_get_config_returns_appconfig(self):
        cfg = get_config()
        assert isinstance(cfg, AppConfig)

    def test_get_config_is_singleton(self):
        assert get_config() is get_config()


class TestUpdateConfig:
    def test_update_writing_model(self, mock_config):
        update_config({"writing_model": "gpt-4o"})
        assert get_config().writing_model == "gpt-4o"

    def test_update_openai_credentials(self, mock_config):
        update_config({"openai": {"api_key": "sk-test", "model": "gpt-4"}})
        assert get_config().openai.api_key == "sk-test"
        assert get_config().openai.model == "gpt-4"

    def test_update_partial_openai(self, mock_config):
        update_config({"openai": {"api_key": "sk-test"}})
        assert get_config().openai.api_key == "sk-test"
        assert get_config().openai.model == "gpt-4o-mini"  # unchanged

    def test_update_multiple_fields(self, mock_config):
        update_config({
            "claude": {"api_key": "sk-ant-test"},
            "writing_model": "claude-opus-4-20250514",
            "polishing_model": "claude-sonnet-4-20250514",
        })
        cfg = get_config()
        assert cfg.claude.api_key == "sk-ant-test"
        assert cfg.writing_model == "claude-opus-4-20250514"
        assert cfg.polishing_model == "claude-sonnet-4-20250514"
