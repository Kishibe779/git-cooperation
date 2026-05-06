from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProviderResult:
    summary: str
    optimized_summary: str
    strengths: list[str]
    risks: list[str]
    suggestion_sections: list[dict[str, list[str] | str]]
    tailored_bullets: list[str]
    provider_used: str
    model_used: str | None = None
    fallback_used: bool = False
    llm_enabled: bool = False


class SuggestionProvider(ABC):
    @abstractmethod
    def generate(self, context: dict, fallback: ProviderResult) -> ProviderResult:
        raise NotImplementedError
