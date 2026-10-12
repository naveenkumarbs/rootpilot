from app.llm.factory import LLMProviderfactory
from app.llm.models import LLMMessage
from app.tools.definitions import RCA_TOOLS

def main():
    provider = LLMProviderfactory.create()
    messages = [
        LLMMessage(
            role="user",
            content=(
                "Investigate recent checkout service errors. "
                "Use available tools."
            )
        )
    ]

    response = provider.generate(
        messages=messages,
        tools=RCA_TOOLS,
        max_output_tokens=2048
    )

    print("\n===== LLM Provider Test =====")
    print("Text:", response.text)
    print("Tool Calls:")
    for call in response.tool_calls:
        print("Name:", call.name)
        print("Arguments", call.arguments)

    print("\nToken Usage:")
    print("Input:", response.input_tokens)
    print("Output:", response.output_tokens)
    print("Reasoning:", response.reasoning_tokens)

    print("Finish Reason:", response.finish_reason)

if __name__ == "__main__":
    main()