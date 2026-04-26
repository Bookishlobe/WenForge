from openai import OpenAI as OpenAIClient
from providers.base import BaseProvider, GenerateParams, GenerateResult
from config import get_config


class OpenAIProvider(BaseProvider):
    """OpenAI / OpenAI-compatible provider."""

    @property
    def name(self) -> str:
        return "openai"

    def _get_client(self) -> OpenAIClient:
        cfg = get_config().openai
        if cfg.endpoint:
            return OpenAIClient(api_key=cfg.api_key, base_url=cfg.endpoint)
        return OpenAIClient(api_key=cfg.api_key)

    def generate(self, params: GenerateParams) -> GenerateResult:
        client = self._get_client()
        cfg = get_config().openai
        model = params.model or cfg.model

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
        usage = response.usage

        # Estimate cost (approximate)
        input_cost = 0
        output_cost = 0
        if "gpt-4o-mini" in model:
            input_cost = 0.15 / 1_000_000
            output_cost = 0.60 / 1_000_000
        elif "gpt-4o" in model:
            input_cost = 2.50 / 1_000_000
            output_cost = 10.00 / 1_000_000

        cost = 0
        if usage:
            cost = (usage.prompt_tokens * input_cost) + (usage.completion_tokens * output_cost)

        return GenerateResult(
            text=text,
            token_count=usage.total_tokens if usage else 0,
            cost=cost,
            model=model,
        )

    def count_tokens(self, text: str) -> int:
        # Rough estimation for Chinese text: ~1.5 tokens per character
        return int(len(text) * 1.5)
