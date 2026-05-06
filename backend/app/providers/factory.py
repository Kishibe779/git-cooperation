from app.core.config import ProviderSettings
from app.providers.base import SuggestionProvider
from app.providers.deepseek_provider import DeepSeekSuggestionProvider
from app.providers.mock_provider import MockSuggestionProvider


def build_provider(settings: ProviderSettings) -> SuggestionProvider:
    if settings.provider == "deepseek":
        return DeepSeekSuggestionProvider(settings)
    return MockSuggestionProvider()
