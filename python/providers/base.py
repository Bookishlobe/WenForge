from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel


class GenerateParams(BaseModel):
    messages: list[dict]  # [{"role": "user"/"assistant", "content": "..."}]
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False
    model: str = ""
    system: Optional[str] = None


class GenerateResult(BaseModel):
    text: str
    token_count: int = 0
    cost: float = 0.0
    model: str = ""


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, params: GenerateParams) -> GenerateResult:
        """Generate text from the LLM."""
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
