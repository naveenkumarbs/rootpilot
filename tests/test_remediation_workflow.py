
import asyncio

from app.workflows.rca_workflow import build_rca_workflow
from app.remediation.models import RemediationPlan, RemediationAction


class FakeRCAAgent:
    async def investigate(self, prompt):
        return {
            "status": "partial",
            "completion_reason": "investigation_saturated",
            "rca_report": {
                "title": "Checkout timeout",
                "confirmed_findings": [
                    {
                        "finding_id": "F-001",
                        "description": "Checkout timed out calling email.",
                        "evidence_ids": ["EV-0001"],
                    }
                ],
                "hypotheses": [],
            },
        }


class FakeRemediationAgent:
    async def plan(self, report):
        return RemediationPlan(
            incident_summary="Checkout timeout",
            actions=[
                RemediationAction(
                    action_type="inspect_service_health",
                    target_service="email",
                    rationale="Investigate downstream timeout.",
                    risk_level="low",
                    supporting_evidence_ids=["EV-0001"],
                )
            ],
        )


async def main():
    graph = build_rca_workflow(
        agent=FakeRCAAgent(),
        remediation_agent=FakeRemediationAgent(),
    )

    result = await graph.ainvoke({
        "incident": "Investigate checkout timeout."
    })

    plan = result["remediation_plan"]

    assert len(plan["actions"]) == 1
    assert plan["actions"][0]["target_service"] == "email"
    assert plan["actions"][0]["action_type"] == "inspect_service_health"

    print("PASS: RCA Agent executed")
    print("PASS: Remediation Agent executed")
    print("PASS: Structured remediation plan generated")
    print("PASS: Multi-agent LangGraph workflow completed")


if __name__ == "__main__":
    asyncio.run(main())
