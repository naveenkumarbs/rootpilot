from typing import TypeVar, Type
from pydantic import BaseModel 

from abc import ABC, abstractmethod

from app.llm.models import (
    LLMResponse,
    LLMMessage,
    ToolDefinition
)

T = TypeVar("T", bound=BaseModel)

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

    def generate_structured(
        self,
        messages: list[LLMMessage],
        response_model: Type[T],
        max_output_tokens: int = 4096,
    ) -> tuple[T, LLMResponse]:
        """
        Generate a structured response confirming to a Pydantic model.

        Returns:
            Rarsed Pydantic object and provider response metadata.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not support structured output"
        )