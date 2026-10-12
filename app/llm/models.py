from dataclasses import dataclass, field
from typing import Any, Literal

@dataclass
class ToolCall:
    id: str
    name: str 
    arguments: dict[str, Any]

@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]

@dataclass
class ToolResult:
    tool_call_id: str
    name: str
    result: Any
    is_error: bool = False

@dataclass
class LLMMessage:
    role: Literal["system","user","assistant","tool"]
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    provider_metadata: dict[str, Any] = field(default_factory=dict)
    
@dataclass
class LLMResponse:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)

    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0

    finish_reason: str | None = None 

    # Provider-specific response data, retained when necessary
    provider_metadata: dict[str, Any] = field(default_factory=dict)
    

