
from uuid import uuid4

from langgraph.types import Command

from app.workflows.approval_workflow import build_approval_workflow


PLAN = {
    "incident_summary": "Checkout timeout",
    "actions": [
        {
            "action_type": "inspect_service_health",
            "target_service": "email",
            "rationale": "Investigate downstream timeout",
            "risk_level": "low",
            "supporting_evidence_ids": ["EV-0001"],
        }
    ],
}


def run_scenario(graph, approved: bool):
    config = {
        "configurable": {
            "thread_id": str(uuid4())
        }
    }

    result = graph.invoke(
        {
            "remediation_plan": PLAN,
            "valid_evidence_ids": ["EV-0001"],
            "allowed_services": ["email", "checkout"],
        },
        config=config,
    )

    assert "__interrupt__" in result
    assert result["policy_allowed"] is True
    assert "execution_status" not in result

    print("\nWorkflow paused for approval")

    result = graph.invoke(
        Command(resume=approved),
        config=config,
    )

    expected = "simulated" if approved else "rejected"

    assert result["approved"] is approved
    assert result["execution_status"] == expected

    print(f"PASS: Approval={approved}, status={expected}")


def test_policy_rejection(graph):
    config = {
        "configurable": {
            "thread_id": str(uuid4())
        }
    }

    result = graph.invoke(
        {
            "remediation_plan": {
                "incident_summary": "No actions",
                "actions": [],
            },
            "valid_evidence_ids": ["EV-0001"],
            "allowed_services": ["email", "checkout"],
        },
        config=config,
    )

    assert result["policy_allowed"] is False
    assert result["execution_status"] == "rejected"
    assert "__interrupt__" not in result

    print("PASS: Invalid plan rejected without approval")


if __name__ == "__main__":
    graph = build_approval_workflow()

    run_scenario(graph, approved=True)
    run_scenario(graph, approved=False)
    test_policy_rejection(graph)

    print("\nPASS: Human approval workflow validated")
