
import asyncio
from uuid import uuid4

from langgraph.types import Command

from app.remediation.models import (
    RemediationPlan,
    RemediationAction,
)
from app.workflows.rootpilot_pipeline import (
    build_rootpilot_pipeline,
)


class FakeRCAAgent:
    def __init__(self):
        self.calls = 0

    async def investigate(self, prompt):
        self.calls += 1

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
    def __init__(self, actions=True):
        self.calls = 0
        self.actions = actions

    async def plan(self, report):
        self.calls += 1

        proposed_actions = []

        if self.actions:
            proposed_actions.append(
                RemediationAction(
                    action_type="inspect_service_health",
                    target_service="email",
                    rationale="Investigate downstream timeout.",
                    risk_level="low",
                    supporting_evidence_ids=["EV-0001"],
                )
            )

        return RemediationPlan(
            incident_summary="Checkout timeout",
            actions=proposed_actions,
        )


async def run_approval_scenario(approved):
    rca = FakeRCAAgent()
    planner = FakeRemediationAgent()

    graph = build_rootpilot_pipeline(
        rca_agent=rca,
        remediation_agent=planner,
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
    assert result["policy_allowed"] is True
    assert "execution_status" not in result

    assert rca.calls == 1
    assert planner.calls == 1

    print("\nWorkflow paused for human approval")

    result = await graph.ainvoke(
        Command(resume=approved),
        config=config,
    )

    expected = "simulated" if approved else "rejected"

    assert result["approved"] is approved
    assert result["execution_status"] == expected

    # Resuming must not rerun the RCA or planning agents.
    assert rca.calls == 1
    assert planner.calls == 1

    print(
        f"PASS: Approval={approved}, "
        f"execution_status={expected}"
    )


async def run_policy_rejection():
    rca = FakeRCAAgent()
    planner = FakeRemediationAgent(actions=False)

    graph = build_rootpilot_pipeline(
        rca_agent=rca,
        remediation_agent=planner,
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

    assert result["policy_allowed"] is False
    assert result["execution_status"] == "rejected"
    assert "__interrupt__" not in result

    print("PASS: Invalid plan rejected before approval")


async def main():
    await run_approval_scenario(approved=True)
    await run_approval_scenario(approved=False)
    await run_policy_rejection()

    print("\nPASS: RootPilot end-to-end workflow validated")


if __name__ == "__main__":
    asyncio.run(main())
