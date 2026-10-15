
from app.remediation.models import RemediationPlan, RemediationAction
from app.remediation.policy import RemediationPolicy


def main():
    plan = RemediationPlan(
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

    decision = RemediationPolicy().validate(
        plan,
        valid_evidence_ids=["EV-0001"],
        allowed_services={"email", "checkout"}
    )

    print("Policy allowed:", decision.allowed)
    print("Policy reason:", decision.reason)

    assert decision.allowed is True

    empty_plan = RemediationPlan(
        incident_summary="No evidence",
        actions=[],
    )

    rejected = RemediationPolicy().validate(empty_plan)

    assert rejected.allowed is False

    print("PASS: Valid remediation plan accepted")
    print("PASS: Empty remediation plan rejected")
    print("PASS: Preliminary remediation policy validated")


if __name__ == "__main__":
    main()
