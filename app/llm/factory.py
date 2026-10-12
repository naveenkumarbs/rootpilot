from app.config.settings import settings
from app.llm.base import LLMProvider
from app.llm.gemini_provider import GeminiProvider

class LLMProviderfactory:
    @staticmethod 
    def create() -> LLMProvider:
        provider_name = settings.llm_provider.lower()
        if provider_name == "gemini":
            return GeminiProvider()
        if provider_name == "claude":
            raise NotImplementedError(
                "Claude API provider is not implemented yet"
            )
        if provider_name == "claude_vertex":
            raise NotImplementedError(
                "Claude Vertex provider is not implemented yet"
            )

        raise ValueError(
            f"Unsupported LLM Provider: {provider_name}"
        )