"""Configuration for the Python sidecar.

Settings are passed from the Electron frontend via API calls,
stored in memory for the session.
"""

from typing import Optional
from pydantic import BaseModel


class ProviderConfig(BaseModel):
    api_key: str = ""
    model: str = "gpt-4o-mini"
    endpoint: Optional[str] = None


class AppConfig(BaseModel):
    openai: ProviderConfig = ProviderConfig()
    claude: ProviderConfig = ProviderConfig()
    deepseek: ProviderConfig = ProviderConfig(endpoint="https://api.deepseek.com")
    local: ProviderConfig = ProviderConfig(endpoint="http://localhost:11434")

    # Model routing
    writing_model: str = "claude-haiku-3-5-20251022"
    polishing_model: str = "claude-opus-4-20250514"

    # Quality tier model routing (A/B/C chapter tiers)
    tier_a_model: str = "claude-opus-4-20250514"
    tier_b_model: str = "claude-haiku-3-5-20251022"
    tier_c_model: str = ""

    # Budget tracking
    monthly_budget_limit: float = 50.0
    current_monthly_cost: float = 0.0

    # Style settings
    style_profile_enabled: bool = False
    style_samples: list[str] = []


# Singleton config (updated via /api/configure endpoint)
_config = AppConfig()


def get_config() -> AppConfig:
    return _config


def update_config(data: dict) -> AppConfig:
    if "openai" in data:
        _config.openai = ProviderConfig(**_config.openai.model_dump() | data["openai"])
    if "claude" in data:
        _config.claude = ProviderConfig(**_config.claude.model_dump() | data["claude"])
    if "deepseek" in data:
        _config.deepseek = ProviderConfig(**_config.deepseek.model_dump() | data["deepseek"])
    if "local" in data:
        _config.local = ProviderConfig(**_config.local.model_dump() | data["local"])
    if "writing_model" in data:
        _config.writing_model = data["writing_model"]
    if "polishing_model" in data:
        _config.polishing_model = data["polishing_model"]
    if "tier_a_model" in data:
        _config.tier_a_model = data["tier_a_model"]
    if "tier_b_model" in data:
        _config.tier_b_model = data["tier_b_model"]
    if "tier_c_model" in data:
        _config.tier_c_model = data["tier_c_model"]
    if "monthly_budget_limit" in data:
        _config.monthly_budget_limit = data["monthly_budget_limit"]
    if "current_monthly_cost" in data:
        _config.current_monthly_cost = data["current_monthly_cost"]
    return _config
