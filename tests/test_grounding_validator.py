from datetime import datetime, timezone

from app.rca.evidence_store import EvidenceStore
from app.rca.grounding_validator import GroundingValidator
from app.rca.models import (
    RCAAnalysis,
    Finding,
    Confidence,
)

from app.rca.models import Hypothesis


def make_store(message: str) -> tuple[EvidenceStore, str]:

    store = EvidenceStore()

    evidence = store.add_log(
        log={
            "timestamp": "2026-10-13T14:01:18Z",
            "service": "checkout",
            "severity": "WARN",
            "message": message,
        },
        tool_name="search_service_logs",
        tool_arguments={
            "service_name": "checkout",
        },
    )

    return store, evidence.evidence_id


def make_analysis(
    statement: str,
    evidence_id: str,
) -> RCAAnalysis:

    return RCAAnalysis(
        title="Checkout incident",
        services_investigated=["checkout", "email"],
        observations=[],
        confirmed_findings=[
            Finding(
                finding_id="F-0001",
                statement=statement,
                evidence_ids=[evidence_id],
                confidence=Confidence.HIGH,
            )
        ],
        hypotheses=[],
        limitations=[],
        recommended_next_steps=[],
    )


def test_supported_timeout():

    store, evidence_id = make_store(
        "Checkout failed to call email: context deadline exceeded"
    )

    analysis = make_analysis(
        "Checkout experienced a timeout while calling email.",
        evidence_id,
    )

    result = GroundingValidator().validate(analysis, store)

    assert result.is_valid
    assert len(result.issues) == 0

    print("PASS: Supported timeout finding")


def test_unsupported_outage():

    store, evidence_id = make_store(
        "Checkout failed to call email: context deadline exceeded"
    )

    analysis = make_analysis(
        "The email service was unavailable.",
        evidence_id,
    )

    result = GroundingValidator().validate(analysis, store)

    assert not result.is_valid

    assert any(
        issue.issue_type == "unsupported_outage_claim"
        for issue in result.issues
    )

    print("PASS: Unsupported outage detected")


def test_unsupported_recovery():

    store, evidence_id = make_store(
        "Order confirmation email sent successfully"
    )

    analysis = make_analysis(
        "The email service recovered.",
        evidence_id,
    )

    result = GroundingValidator().validate(analysis, store)

    assert not result.is_valid

    assert any(
        issue.issue_type == "unsupported_recovery_claim"
        for issue in result.issues
    )

    print("PASS: Unsupported recovery detected")


def test_causality_warning():

    store, evidence_id = make_store(
        "Checkout request failed: context deadline exceeded"
    )

    analysis = make_analysis(
        "The checkout failure was caused by email service overload.",
        evidence_id,
    )

    result = GroundingValidator().validate(analysis, store)

    assert result.is_valid

    assert any(
        issue.issue_type == "possible_unsupported_causality"
        for issue in result.issues
    )

    print("PASS: Causality warning generated")

def test_unverified_hypothesis_allowed():

    store, evidence_id = make_store(
        "Checkout failed to call email: context deadline exceeded"
    )

    analysis = RCAAnalysis(
        title="Checkout incident",
        services_investigated=["checkout", "email"],
        observations=[],
        confirmed_findings=[],
        hypotheses=[
            Hypothesis(
                hypothesis_id="H-0001",
                statement=(
                    "Email service latency may have contributed "
                    "to the checkout timeout."
                ),
                confidence=Confidence.LOW,
                supporting_evidence_ids=[evidence_id],
                contradicting_evidence_ids=[],
                validation_steps=[
                    "Inspect email-service latency metrics.",
                    "Correlate checkout and email traces.",
                ],
            )
        ],
        limitations=[
            "No email-service latency metrics were available."
        ],
        recommended_next_steps=[],
    )

    result = GroundingValidator().validate(analysis, store)

    assert result.is_valid
    assert result.checked_findings == 0

    print("PASS: Unverified hypothesis allowed")

def main():

    test_supported_timeout()
    test_unsupported_outage()
    test_unsupported_recovery()
    test_causality_warning()
    test_unverified_hypothesis_allowed()

    print("\nAll grounding validator tests passed.")


if __name__ == "__main__":
    main()