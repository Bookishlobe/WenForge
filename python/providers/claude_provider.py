from anthropic import Anthropic
from providers.base import BaseProvider, GenerateParams, GenerateResult
from config import get_config


class ClaudeProvider(BaseProvider):
    """Anthropic Claude provider."""

    @property
    def name(self) -> str:
        return "claude"

    def _get_client(self) -> Anthropic:
        cfg = get_config().claude
        kwargs = {"api_key": cfg.api_key}
        if cfg.endpoint:
            kwargs["base_url"] = cfg.endpoint
        return Anthropic(**kwargs)

    def generate(self, params: GenerateParams) -> GenerateResult:
        client = self._get_client()
        cfg = get_config().claude
        model = params.model or cfg.model

        # Convert messages to Anthropic format
        system = params.system
        anthropic_messages = []
        for msg in params.messages:
            if msg["role"] == "system":
                system = (system or "") + "\n" + msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        response = client.messages.create(
            model=model,
            messages=anthropic_messages or [{"role": "user", "content": "Hello"}],
            system=system,
            temperature=params.temperature,
            max_tokens=params.max_tokens,
        )

        text = "".join(block.text for block in response.content if hasattr(block, 'text'))

        # Estimate cost (approximate)
        input_cost = 0
        output_cost = 0
        if "haiku" in model:
            input_cost = 0.80 / 1_000_000
            output_cost = 4.00 / 1_000_000
        elif "sonnet" in model:
            input_cost = 3.00 / 1_000_000
            output_cost = 15.00 / 1_000_000
        elif "opus" in model:
            input_cost = 15.00 / 1_000_000
            output_cost = 75.00 / 1_000_000

        cost = 0
        if response.usage:
            cost = (response.usage.input_tokens * input_cost) + (response.usage.output_tokens * output_cost)

        return GenerateResult(
            text=text,
            token_count=(response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0,
            cost=cost,
            model=model,
        )

    def count_tokens(self, text: str) -> int:
        # Rough estimation for Chinese text
        return int(len(text) * 1.5)
