from openai import OpenAI as OpenAIClient
from providers.base import BaseProvider, GenerateParams, GenerateResult
from config import get_config


class DeepSeekProvider(BaseProvider):
    """DeepSeek provider (OpenAI-compatible API)."""

    @property
    def name(self) -> str:
        return "deepseek"

    def _get_client(self) -> OpenAIClient:
        cfg = get_config().deepseek
        base_url = cfg.endpoint or "https://api.deepseek.com"
        return OpenAIClient(api_key=cfg.api_key, base_url=base_url)

    def generate(self, params: GenerateParams) -> GenerateResult:
        client = self._get_client()
        cfg = get_config().deepseek
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

        # DeepSeek pricing (approximate, per million tokens)
        input_cost = 0
        output_cost = 0
        model_lower = model.lower()
        if "deepseek-v4-flash" in model_lower:
            input_cost = 0.15 / 1_000_000
            output_cost = 0.60 / 1_000_000
        elif "deepseek-v4-pro" in model_lower:
            input_cost = 0.50 / 1_000_000
            output_cost = 2.00 / 1_000_000
        elif "deepseek-chat" in model_lower:
            input_cost = 0.27 / 1_000_000
            output_cost = 1.10 / 1_000_000
        elif "deepseek-reasoner" in model_lower:
            input_cost = 0.55 / 1_000_000
            output_cost = 2.19 / 1_000_000
        else:
            input_cost = 0.50 / 1_000_000
            output_cost = 2.00 / 1_000_000

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
