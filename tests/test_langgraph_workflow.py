import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from app.workflows.rootpilot_graph import build_rootpilot_graph

def main():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("Gemini API key not configured.")

    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        api_key=api_key,
        temperature=0,
    )

    graph = build_rootpilot_graph(llm)

    result = graph.invoke({
        "incident": (
            "Checkout service experienced a timeout while calling "
            "the email service at 2026-10-14 14:01:18 UTC."
        ),
        "prepared_incident": "",
        "summary": "",
    })

    print("\n===== LANGGRAPH RESULT =====")
    print("Incident:", result["incident"])
    print("Prepared:", result["prepared_incident"])
    print("Summary:", result["summary"])

    assert result["prepared_incident"]
    assert result["summary"].strip()

    print("\nPASS: LangGraph workflow executed successfully")

if __name__ == "__main__":
    main()