"""Local model provider via Ollama API (OpenAI-compatible)."""

from openai import OpenAI as OpenAIClient
from providers.base import BaseProvider, GenerateParams, GenerateResult
from config import get_config


class LocalProvider(BaseProvider):
    """Local model provider via Ollama."""

    @property
    def name(self) -> str:
        return "local"

    def _get_client(self) -> OpenAIClient:
        cfg = get_config().local
        endpoint = cfg.endpoint or "http://localhost:11434"
        # Ollama uses OpenAI-compatible endpoint
        api_base = endpoint.rstrip("/") + "/v1"
        return OpenAIClient(api_key="ollama", base_url=api_base)

    def generate(self, params: GenerateParams) -> GenerateResult:
        client = self._get_client()
        cfg = get_config().local
        model = params.model or cfg.model or "qwen2.5:7b"

        kwargs = {
            "model": model,
            "messages": params.messages,
            "temperature": params.temperature,
            "max_tokens": params.max_tokens,
        }
        if params.system:
            kwargs["messages"] = [{"role": "system", "content": params.system}] + params.messages

        response = client.chat.completions.create(**kwargs)
        text = response.choices[0].message.content or ""

        return GenerateResult(
            text=text,
            token_count=0,
            cost=0,
            model=model,
        )

    def count_tokens(self, text: str) -> int:
        return int(len(text) * 1.5)
