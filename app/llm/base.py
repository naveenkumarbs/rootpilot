from abc import ABC, abstractmethod

from app.llm.models import (
    LLMResponse,
    LLMMessage,
    ToolDefinition
)

class LLMProvider(ABC):
    @abstractmethod
    def generate(
        self, 
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
        max_output_tokens: int = 2048        
    ) -> LLMResponse:
        """
        Generate an LLM response.
        
        tools=None:
            Text-only generation.
        tools=[...]:
            Tool calling is available
        """
        pass