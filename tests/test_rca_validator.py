from datetime import datetime, timezone

from app.rca.evidence_store import EvidenceStore
from app.rca.models import (
    RCAAnalysis,
    Finding,
    Observation,
    Hypothesis,
    Confidence,
)
from app.rca.validator import EvidenceValidator


def test_unknown_evidence_id():

    store = EvidenceStore()

    analysis = RCAAnalysis(
        title="Checkout Investigation",
        confirmed_findings=[
            Finding(
                finding_id="FIND-0001",
                statement="Checkout experienced timeouts.",
                evidence_ids=["EV-9999"],
                confidence=Confidence.HIGH,
            )
        ],
    )

    result = EvidenceValidator().validate(analysis, store)

    # print("Evidence count:", store.count())
    # print("Findings:", analysis.confirmed_findings)
    # print("Validation result:", result)
    # print("Validation errors:", result.errors)

    assert result.is_valid is False
    assert any("EV-9999" in error for error in result.errors)

    print("PASS: Unknown evidence ID rejected")


def test_valid_evidence_id():

    store = EvidenceStore()

    evidence = store.add_log(
        log={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "checkout",
            "severity": "ERROR",
            "message": "Checkout request timed out",
        },
        tool_name="search_service_logs",
        tool_arguments={
            "service_name": "checkout",
            "minutes": 10,
            "limit": 10,
        },
    )

    analysis = RCAAnalysis(
        title="Checkout Investigation",
        observations=[
            Observation(
                observation_id="OBS-0001",
                statement="A checkout timeout was logged.",
                evidence_ids=[evidence.evidence_id],
            )
        ],
        confirmed_findings=[
            Finding(
                finding_id="FIND-0001",
                statement="Checkout emitted a timeout error.",
                evidence_ids=[evidence.evidence_id],
                confidence=Confidence.HIGH,
            )
        ],
        hypotheses=[
            Hypothesis(
                hypothesis_id="HYP-0001",
                statement="A downstream dependency may be slow.",
                confidence=Confidence.LOW,
                supporting_evidence_ids=[evidence.evidence_id],
                contradicting_evidence_ids=[],
                validation_steps=[
                    "Inspect downstream service latency metrics."
                ],
            )
        ],
    )

    result = EvidenceValidator().validate(analysis, store)

    assert result.is_valid is True
    assert result.errors == []

    print("PASS: Valid evidence references accepted")


def test_empty_evidence():

    store = EvidenceStore()

    analysis = RCAAnalysis(
        title="Checkout Investigation",
    )

    result = EvidenceValidator().validate(analysis, store)

    assert result.is_valid is True
    assert result.errors == []
    assert len(result.warnings) == 2

    print("PASS: Empty evidence produces warnings")

def test_invalid_references_in_all_components():
    store = EvidenceStore()
    analysis = RCAAnalysis(
        title = "Invalid Reference Investigation",
        observations=[
            Observation(
                observation_id="OBS-0001",
                statement="An error occured.",
                evidence_ids=["EV-9001"],
            )
        ],
        confirmed_findings=[
            Finding(
                finding_id="FIND-0001",
                statement="Checkout failed.",
                evidence_ids=["EV-9002"],
                confidence=Confidence.HIGH,
            )
        ],

        hypotheses = [
            Hypothesis(
                hypothesis_id="HYP-0001",
                statement="Downstream latency may be responsible.",
                confidence=Confidence.MEDIUM,
                supporting_evidence_ids=["EV-9003"],
                contradicting_evidence_ids=["EV-9004"],
            )
        ],
    )

    result=EvidenceValidator().validate(analysis,store)

    assert result.is_valid is False
    errors_text = " ".join(result.errors)

    for evidence_id in ["EV-9001", "EV-9002", "EV-9003", "EV-9004"]:
        assert evidence_id in errors_text
    
    assert(len(result.errors) == 4)

    print("PASS: All evidence reference fields validated")

def test_hypothesis_without_evidence():
    store = EvidenceStore()

    analysis = RCAAnalysis(
        title="Investigation With Unverified Hypothesis",

        hypotheses=[
            Hypothesis(
                hypothesis_id="HYP-0001",
                statement="Network latency may have caused the timeout.",
                confidence=Confidence.LOW,
                supporting_evidence_ids=[],
                contradicting_evidence_ids=[],
                validation_steps=[
                    "Inspect network latency metrics."
                ],
            )
        ],
    )

    result = EvidenceValidator().validate(analysis, store)

    assert result.is_valid is True
    assert result.errors == []

    print("PASS: Unverified hypotheses are permitted")


def main():

    test_unknown_evidence_id()
    test_valid_evidence_id()
    test_empty_evidence()
    test_invalid_references_in_all_components()
    test_hypothesis_without_evidence()

    print("\nAll EvidenceValidator tests passed.")


if __name__ == "__main__":
    main()