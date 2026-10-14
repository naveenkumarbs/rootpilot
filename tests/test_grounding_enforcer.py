from app.rca.grounding_enforcer import (
    GroundingEnforcer,
    EnforcementDecision,
)

from app.rca.models import (
    RCAAnalysis,
    Finding,
    Confidence,
)


def make_analysis():

    return RCAAnalysis(
        title="Checkout incident",
        services_investigated=["checkout", "email"],
        observations=[],
        confirmed_findings=[
            Finding(
                finding_id="FND-001",
                statement="Checkout experienced a timeout.",
                evidence_ids=["EV-0001"],
                confidence=Confidence.HIGH,
            ),
            Finding(
                finding_id="FND-002",
                statement="Email service caused the timeout.",
                evidence_ids=["EV-0002"],
                confidence=Confidence.MEDIUM,
            ),
        ],
        hypotheses=[],
        limitations=[],
        recommended_next_steps=[],
    )


def make_audit(
    first="supported",
    second="partially_supported",
    issues=None,
    semantic_status="completed",
):

    if issues is None:
        issues = []

    return {
        "status": "completed",
        "deterministic": {
            "is_valid": True,
            "checked_findings": 2,
            "issues": issues,
        },
        "semantic": {
            "status": semantic_status,
            "evaluations": [
                {
                    "finding_id": "FND-001",
                    "classification": first,
                },
                {
                    "finding_id": "FND-002",
                    "classification": second,
                },
            ],
        },
    }


def valid_evidence():

    return {
        "is_valid": True,
        "errors": [],
        "warnings": [],
    }


def test_supported_and_partial():

    result = GroundingEnforcer().enforce(
        analysis=make_analysis(),
        grounding_audit=make_audit(),
        evidence_validation=valid_evidence(),
    )
    
    assert result.confirmed_count == 1
    assert result.provisional_count == 1
    assert result.rejected_count == 0

    assert result.confirmed_findings[0].finding_id == "FND-001"
    assert result.provisional_findings[0].finding_id == "FND-002"

    print("PASS: Supported and partial findings")


def test_unsupported_rejected():

    result = GroundingEnforcer().enforce(
        analysis=make_analysis(),
        grounding_audit=make_audit(second="unsupported"),
        evidence_validation=valid_evidence(),
    )

    assert result.rejected_count == 1
    assert result.rejected_findings[0].finding_id == "FND-002"

    print("PASS: Unsupported finding rejected")


def test_deterministic_warning():

    issues = [
        {
            "finding_id": "FND-001",
            "issue_type": "possible_unsupported_causality",
            "severity": "warning",
        }
    ]

    result = GroundingEnforcer().enforce(
        analysis=make_analysis(),
        grounding_audit=make_audit(issues=issues),
        evidence_validation=valid_evidence(),
    )

    assert result.provisional_count == 2

    print("PASS: Deterministic warning enforced")


def test_blocking_error():

    issues = [
        {
            "finding_id": "FND-001",
            "issue_type": "unsupported_outage_claim",
            "severity": "error",
        }
    ]

    result = GroundingEnforcer().enforce(
        analysis=make_analysis(),
        grounding_audit=make_audit(issues=issues),
        evidence_validation=valid_evidence(),
    )

    assert result.rejected_count == 1

    assert (
        result.rejected_findings[0].finding_id
        == "FND-001"
    )

    print("PASS: Blocking error enforced")


def test_semantic_unavailable():

    result = GroundingEnforcer().enforce(
        analysis=make_analysis(),
        grounding_audit=make_audit(
            semantic_status="timeout"
        ),
        evidence_validation=valid_evidence(),
    )

    assert result.confirmed_count == 0
    assert result.provisional_count == 2

    print("PASS: Missing semantic evaluation handled")


def test_invalid_evidence():

    result = GroundingEnforcer().enforce(
        analysis=make_analysis(),
        grounding_audit=make_audit(),
        evidence_validation={
            "is_valid": False,
            "errors": ["Unknown evidence ID"],
            "warnings": [],
        },
    )

    assert result.confirmed_count == 0
    assert result.rejected_count == 2

    print("PASS: Invalid evidence rejected")

def test_missing_deterministic_evaluation():

    audit = make_audit(
        first="supported",
        second="supported",
    )

    audit["deterministic"] = None

    result = GroundingEnforcer().enforce(
        analysis=make_analysis(),
        grounding_audit=audit,
        evidence_validation=valid_evidence(),
    )

    assert result.confirmed_count == 0
    assert result.provisional_count == 2

    print("PASS: Missing deterministic evaluation fails closed")

def test_duplicate_semantic_evaluations():

    audit = make_audit()

    audit["semantic"]["evaluations"].append(
        {
            "finding_id": "FND-001",
            "classification": "supported",
        }
    )

    result = GroundingEnforcer().enforce(
        analysis=make_analysis(),
        grounding_audit=audit,
        evidence_validation=valid_evidence(),
    )

    assert result.confirmed_count == 0
    assert result.provisional_count == 2

    print("PASS: Duplicate semantic evaluations rejected")

def test_missing_finding_evaluation():

    audit = make_audit()

    audit["semantic"]["evaluations"] = [
        {
            "finding_id": "FND-001",
            "classification": "supported",
        }
    ]

    result = GroundingEnforcer().enforce(
        analysis=make_analysis(),
        grounding_audit=audit,
        evidence_validation=valid_evidence(),
    )

    assert result.confirmed_count == 0
    assert result.provisional_count == 2

    print("PASS: Incomplete semantic evaluation fails closed")

def test_unknown_classification():

    audit = make_audit()

    audit["semantic"]["evaluations"][0][
        "classification"
    ] = "definitely_correct"

    result = GroundingEnforcer().enforce(
        analysis=make_analysis(),
        grounding_audit=audit,
        evidence_validation=valid_evidence(),
    )

    assert result.confirmed_count == 0
    assert result.provisional_count == 2

    print("PASS: Unknown semantic classification rejected")

def test_unknown_deterministic_severity():

    audit = make_audit(
        first="supported",
        second="supported",
    )

    audit["deterministic"]["issues"] = [
        {
            "finding_id": "FND-001",
            "issue_type": "unsupported_causality",
            "severity": "critical",
        }
    ]

    result = GroundingEnforcer().enforce(
        analysis=make_analysis(),
        grounding_audit=audit,
        evidence_validation=valid_evidence(),
    )

    assert result.confirmed_count == 0
    assert result.provisional_count == 2

    print("PASS: Unknown deterministic severity fails closed")

def test_unknown_finding_reference():

    audit = make_audit()

    audit["semantic"]["evaluations"][0][
        "finding_id"
    ] = "FND-999"

    result = GroundingEnforcer().enforce(
        analysis=make_analysis(),
        grounding_audit=audit,
        evidence_validation=valid_evidence(),
    )

    assert result.confirmed_count == 0
    assert result.provisional_count == 2

    print("PASS: Unknown finding reference rejected")

def test_all_checks_successful():

    audit = make_audit(
        first="supported",
        second="supported",
    )

    result = GroundingEnforcer().enforce(
        analysis=make_analysis(),
        grounding_audit=audit,
        evidence_validation=valid_evidence(),
    )

    assert result.confirmed_count == 2
    assert result.provisional_count == 0
    assert result.rejected_count == 0

    print("PASS: Valid findings remain confirmed")

def main():

    test_supported_and_partial()
    test_unsupported_rejected()
    test_deterministic_warning()
    test_blocking_error()
    test_semantic_unavailable()
    test_invalid_evidence()
    test_missing_deterministic_evaluation()
    test_duplicate_semantic_evaluations()
    test_missing_finding_evaluation()
    test_unknown_classification()
    test_unknown_deterministic_severity()
    test_unknown_finding_reference()
    test_all_checks_successful()
    
    print("\nAll grounding enforcement tests passed.")


if __name__ == "__main__":
    main()