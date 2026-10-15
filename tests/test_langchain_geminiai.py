import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("Set GOOGLE_API_KEY or GEMINI_API_KEY in your .env file.")

# Use the same Gemini model as RootPilot provider
model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

llm = ChatGoogleGenerativeAI(
    model=model_name,
    api_key=api_key,
    temperature=0,
    max_retries=2,
)

messages = [
    SystemMessage(
        content="You are RootPilot, an incident investigation assistant."
    ),
    HumanMessage(
        content=(
            "A checkout service timed out while calling an email service. "
            "List two possible causes. Do not claim either is confirmed."
        )
    ),
]

response = llm.invoke(messages)

print("\n===== LANGCHAIN RESPONSE =====")
print(response.text)

print("\n===== TOKEN USAGE =====")
print(response.usage_metadata)

assert response.text.strip(), "Gemini returned an empty response."

print("\nPASS: LangChain Gemini integration successful")