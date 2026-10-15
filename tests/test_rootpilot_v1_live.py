
import asyncio
import os
from uuid import uuid4

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.types import Command

from app.agents.rca_agent import RCAAgent
from app.agents.remediation_agent import RemediationPlanningAgent
from app.agents.verification_agent import RemediationVerificationAgent
from app.workflows.rootpilot_pipeline import build_rootpilot_pipeline


async def main():
    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("Gemini API key not configured.")

    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        api_key=api_key,
        temperature=0,
    )

    graph = build_rootpilot_pipeline(
        rca_agent=RCAAgent(),
        remediation_agent=RemediationPlanningAgent(llm),
        verification_agent=RemediationVerificationAgent(llm),
        allowed_services={"checkout", "email"},
    )

    config = {
        "configurable": {
            "thread_id": str(uuid4())
        }
    }

    result = await graph.ainvoke(
        {
            "incident": (
                "Investigate the checkout service timeout "
                "while calling the email service. "
                "Correlate logs and identify supported findings."
            )
        },
        config=config,
    )

    print("\n===== RCA RESULT =====")
    print("Status:", result.get("status"))
    print("Completion reason:", result.get("completion_reason"))

    print("\n===== POLICY RESULT =====")
    print("Allowed:", result.get("policy_allowed"))
    print("Reason:", result.get("policy_reason"))

    if "__interrupt__" in result:
        print("\nHuman approval requested.")

        # For automated testing, reject by default.
        # This exercises the human-approval rejection path.
        result = await graph.ainvoke(
            Command(resume=False),
            config=config,
        )

    print("\n===== FINAL RESULT =====")
    print("Execution:", result.get("execution_status"))
    print("Verification:", result.get("verification_report"))

    assert result.get("execution_status") == "rejected"

    verification = result.get("verification_report", {})

    assert verification.get("production_recovery_verified") is False

    print("\nPASS: RootPilot V1 live integration completed")


if __name__ == "__main__":
    asyncio.run(main())
