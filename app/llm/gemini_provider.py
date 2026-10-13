import uuid
import json
from google import genai
from google.genai import types 

from typing import Type, TypeVar
from pydantic import BaseModel

from app.config.settings import settings
from app.llm.base import LLMProvider
from app.llm.models import (
    LLMResponse,
    LLMMessage,
    ToolCall,
    ToolDefinition
)

T = TypeVar("T", bound=BaseModel)

class GeminiProvider (LLMProvider):
    def __init__(self):
        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured"
            )

        self.client = genai.Client(api_key=settings.gemini_api_key)

        self.model = settings.gemini_model

    def _convert_tools(
            self,
            tools: list[ToolDefinition]
    ) -> list[types.Tool]:
        declarations = []
        for tool in tools:
            declarations.append(
                types.FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters_json_schema=tool.parameters
                )
            )

        return [
            types.Tool(
                function_declarations=declarations
            )
        ]

    def _convert_messages(
            self,
            messages: list[LLMMessage]
    ) -> tuple[list[types.Content], str | None]:
        contents = []
        system_messages = []

        for message in messages:
            if message.role == "system":
                system_messages.append(message.content)
                continue
            if message.role == "user":
                contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(
                                text=message.content
                            )
                        ]
                    )
                )
            elif message.role =="assistant":
                original_content = message.provider_metadata.get("gemini_content")
                if original_content is not None:
                    contents.append(original_content)
                    continue
                
                parts = []

                if message.content:
                    parts.append(
                        types.Part.from_text(
                            text=message.content
                        )
                    )
                for call in message.tool_calls:
                    parts.append(
                        types.Part.from_function_call(
                            name=call.name,
                            args=call.arguments
                        )
                    )
                if parts:
                    contents.append(
                        types.Context(
                            role="model",
                            parts=parts
                        )
                    )
            elif message.role == "tool":
                parts = []
                for result in message.tool_results:
                    parts.append(
                        types.Part.from_function_response(
                            name=result.name,
                            response={
                                "result": result.result,
                                "is_error": result.is_error
                            }
                        )
                    )
                if parts:
                    contents.append(
                        types.Content(
                            role="user",
                            parts=parts
                        )
                    )
        system_instruction = (
            "\n".join(system_messages) if system_messages else None
        )

        return contents, system_instruction

    def generate(
            self, 
            messages: list[LLMMessage],
            tools: list[ToolDefinition] | None = None,
            max_output_tokens: int = 2048
    ) -> LLMResponse :

        contents, system_instruction = self._convert_messages(messages)
        config_kwargs = {
            "temperature": 0.2,
            "max_output_tokens": max_output_tokens
        }

        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        if tools:
            config_kwargs["tools"] = self._convert_tools(tools)
            config_kwargs["automatic_function_calling"] = (
                types.AutomaticFunctionCallingConfig(
                    disable=True
                )
            )
            config_kwargs["tool_config"] = types.ToolConfig(
                function_calling_config=(
                    types.FunctionCallingConfig(
                        mode=types.FunctionCallingConfigMode.AUTO
                    )
                )
            )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                **config_kwargs
            )
        )

        text_parts = []
        tool_calls = []

        if response.candidates:
            candidate=response.candidates[0]
            content=candidate.content
            if content:
                for part in content.parts or []:
                    if part.text:
                        text_parts.append(part.text)
                    if part.function_call:
                        call = part.function_call
                        tool_calls.append(
                            ToolCall(
                                id=str(uuid.uuid4()),
                                name=call.name,
                                arguments=dict(
                                    call.args or {}
                                )
                            )
                        )

        usage = response.usage_metadata
        finish_reason = None
        if response.candidates:
            finish = response.candidates[0].finish_reason
            if finish is not None:
                finish_reason = str(finish)
        
        return LLMResponse(
            text = "\n".join(text_parts),
            tool_calls=tool_calls,
            input_tokens=(
                usage.prompt_token_count if usage else 0
            ) or 0,
            output_tokens=(
                usage.candidates_token_count if usage else 0
            ) or 0,
            reasoning_tokens=(
                usage.thoughts_token_count if usage else 0
            ),
            finish_reason=finish_reason,
            provider_metadata={
                "gemini_content": (
                    response.candidates[0].content
                    if response.candidates else None
                )
            }
        )

    def generate_with_tools(self, contents: list[types.Content]):
        tool = types.FunctionDeclaration(
            name="search_service_logs",
            description=(
                "Search application logs in OpenSearch "
                "for a specified microservice. "
                "Use this tool when investigating service "
                "errors, warnings, failures, or timeouts."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "service_name": types.Schema(
                        type=types.Type.STRING,
                        description="Microservice name, for example checkout"
                    ),
                    "minutes": types.Schema(
                        type=types.Type.INTEGER,
                        description="Log Lookback window in minutes, Allowed range: 1 and 60",
                        minimum=1,
                        maximum=60
                    ),
                    "severity": types.Schema(
                        type=types.Type.STRING,
                        description="Optional log severity filter"
                    ),
                    "limit": types.Schema(
                        type=types.Type.INTEGER,
                        description="Maximum log entries to retrieve. Allowed range: 1 to 50. Prefer 10 to 20.",
                        minimum=1,
                        maximum=50
                    )
                },
                required=["service_name"]
            )
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        function_declarations=[tool]
                    )
                ],
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode=types.FunctionCallingConfigMode.AUTO
                    )
                ),
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
                temperature=0.2,
                max_output_tokens=1024
            )
        )

        # automatic_function_calling is disabled. 
        # VERY IMPORTANT
        # Gemini SDK supports automatic execution of certain python functions when configured for automatic function calling
        # By disabling this, gemini can request but execution remains the responsibility of our tool dispatcher

        return response

    def generate_final_report(
            self,
            contents: list[types.Content]
    ):
        return self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=2048
            )
        )

    def generate_structured(
        self,
        messages: list,
        response_model: Type[T],
        max_output_tokens: int = 4096,
    ) -> tuple[T, LLMResponse]:

        system_instructions = []
        conversation = []

        for message in messages:
            if message.role == "system":
                system_instructions.append(message.content)
            elif message.role == "user":
                conversation.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=message.content)
                        ],
                    )
                )
            else:
                raise ValueError(
                    "Structured generation expects system and user "
                    f"messages only; received role = {message.role!r}"
                )

        if not conversation:
            raise ValueError(
                "Structured generation requires at least one user message"
            )

        raw_schema = response_model.model_json_schema()
        gemini_schema = sanitize_gemini_schema(raw_schema)

        print(
            "Original contains additionalProperties:",
            "additionalProperties" in json.dumps(raw_schema)
        )

        print(
            "Gemini schema contains additionalProperties:",
            "additionalProperties" in json.dumps(gemini_schema)
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=conversation,
            config=types.GenerateContentConfig(
                system_instruction="\n".join(system_instructions) or None,
                response_mime_type="application/json",
                response_schema=gemini_schema,
                max_output_tokens=max_output_tokens,
            ),
        )

        if not response.text:
            raise ValueError(
                "Gemini returned empty structured response"
            )

        parsed = response_model.model_validate_json(response.text)

        usage = response.usage_metadata

        metadata = LLMResponse(
            text=response.text,
            input_tokens=(
                usage.prompt_token_count or 0
            ) if usage else 0,
            output_tokens=(
                usage.candidates_token_count or 0
            ) if usage else 0,
            reasoning_tokens=(
                usage.thoughts_token_count or 0
            ) if usage else 0,
        )

        return parsed, metadata

    
def sanitize_gemini_schema(schema):
    """
    Prepare a Pydantic JSON Schema for Gemini.
    Remove only known incompatible fields.
    Preserve the original Pydantic valdation model.
    """

    if isinstance(schema, dict):
        return{
            key: sanitize_gemini_schema(value) 
            for key, value in schema.items()
            if key != "additionalProperties"
        }
    if isinstance(schema, list):
        return[
            sanitize_gemini_schema(item)
            for item in schema
        ]
    return schema