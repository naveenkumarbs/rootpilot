
import asyncio
from uuid import uuid4

from langgraph.types import Command

from app.workflows.rootpilot_pipeline import build_rootpilot_pipeline
from app.remediation.models import RemediationPlan, RemediationAction
from app.remediation.verification_models import VerificationReport


class FakeRCAAgent:
    async def investigate(self, prompt):
        return {
            "status": "completed",
            "completion_reason": "investigation_completed",
            "rca_report": {
                "title": "Checkout timeout",
                "confirmed_findings": [
                    {
                        "description": "Checkout timed out calling email.",
                        "evidence_ids": ["EV-0001"],
                    }
                ],
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


class FakeVerificationAgent:
    def __init__(self):
        self.calls = 0

    async def verify(self, remediation_plan, execution_status):
        self.calls += 1

        return VerificationReport(
            verification_status=(
                "simulated_only"
                if execution_status == "simulated"
                else "not_executed"
            ),
            observations=[
                f"Execution status: {execution_status}"
            ],
            recommended_next_steps=[
                "Check real service health and error rates."
            ],
            production_recovery_verified=False,
        )


async def run_scenario(approved):
    verifier = FakeVerificationAgent()

    graph = build_rootpilot_pipeline(
        rca_agent=FakeRCAAgent(),
        remediation_agent=FakeRemediationAgent(),
        verification_agent=verifier,
        allowed_services={"email", "checkout"}
    )

    config = {
        "configurable": {
            "thread_id": str(uuid4())
        }
    }

    result = await graph.ainvoke(
        {"incident": "Investigate checkout timeout."},
        config=config,
    )

    assert "__interrupt__" in result
    assert verifier.calls == 0

    result = await graph.ainvoke(
        Command(resume=approved),
        config=config,
    )

    verification = result["verification_report"]

    expected = (
        "simulated_only" if approved else "not_executed"
    )

    assert verifier.calls == 1
    assert verification["verification_status"] == expected
    assert verification["production_recovery_verified"] is False

    print(
        f"PASS: Approval={approved}, "
        f"verification={expected}"
    )


async def main():
    await run_scenario(approved=True)
    await run_scenario(approved=False)

    print("\nPASS: Three-agent RootPilot workflow validated")


if __name__ == "__main__":
    asyncio.run(main())
