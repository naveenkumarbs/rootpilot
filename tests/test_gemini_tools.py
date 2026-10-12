from app.llm.gemini_provider import GeminiProvider

def main():
    provider = GeminiProvider()
    print("Testing Gemini function caling...")
    try:
        response = provider.generate_with_tools(
            "Search the checkout service logs from the last 15 minutes."
        )

        print("\nResponse received.")

        if response.candidates:
            candidate = response.candidates[0]
            print("Finish reason:", candidate.finish_reason)
            if candidate.content:
                for part in candidate.content.parts:
                    print("Tool:", part.function_call.name)
                    print("Arguments:", part.function_call.args or {})
            elif part.text:
                print("Text:", part.text)
    except Exception as exc:
        print("\nGemini request failed.")
        print("Error type:", type(exc).__name__)
        print("Error:", str(exc))

        raise

if __name__ == "__main__":
    main()