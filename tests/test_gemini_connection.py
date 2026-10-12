from app.llm.gemini_provider import GeminiProvider

def main():
    provider = GeminiProvider()

    response = provider.generate(
        "Explain Root Cause Analysis in two sentences."
    )

    print ("\nGemini Response:")
    print(response.text)

    print("\nToken Usage:")
    print("Input:", response.input_tokens)
    print("Output:", response.output_tokens)
    print("Reasoning:", response.reasoning_tokens)

    print("\nFinish Reason:")
    print(response.finish_reason)

if __name__ == "__main__":
    main()