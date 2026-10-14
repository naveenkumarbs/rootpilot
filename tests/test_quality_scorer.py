from app.rca.quality_scorer import RCAQualityScorer


def make_audit(
    classifications=None,
    issues=None,
    semantic_status="completed",
):

    if classifications is None:
        classifications = ["supported"]

    if issues is None:
        issues = []

    evaluations = []

    for index, classification in enumerate(
        classifications,
        start=1,
    ):
        evaluations.append({
            "finding_id": f"FIND-{index:03d}",
            "classification": classification,
            "explanation": "Test evaluation.",
            "supporting_evidence_ids": [
                f"EV-{index:04d}"
            ],
            "unsupported_claims": [],
        })

    return {
        "status": "completed",
        "deterministic": {
            "is_valid": True,
            "checked_findings": len(classifications),
            "issues": issues,
        },
        "semantic": {
            "status": semantic_status,
            "evaluations": evaluations,
        },
    }


def valid_evidence():

    return {
        "is_valid": True,
        "errors": [],
        "warnings": [],
    }


def test_perfect_score():

    result = RCAQualityScorer().score(
        grounding_audit=make_audit(),
        evidence_validation=valid_evidence(),
        confirmed_finding_ids=["FIND-001"],
    )

    assert result.status == "assessed"
    assert result.overall_score == 100.0
    assert result.grade == "A"

    print("PASS: Perfect quality score")


def test_deterministic_warning():

    audit = make_audit(
        issues=[
            {
                "finding_id": "FIND-001",
                "issue_type": "possible_unsupported_causality",
                "severity": "warning",
            }
        ]
    )

    result = RCAQualityScorer().score(
        grounding_audit=audit,
        evidence_validation=valid_evidence(),
        confirmed_finding_ids=["FIND-001"],
    )

    assert result.overall_score == 95.0

    print("PASS: Deterministic warning penalty")


def test_mixed_semantic_classifications():

    audit = make_audit(
        classifications=[
            "supported",
            "partially_supported",
            "unsupported",
            "insufficient_evidence",
        ]
    )

    result = RCAQualityScorer().score(
        grounding_audit=audit,
        evidence_validation=valid_evidence(),
        confirmed_finding_ids=[
            "FIND-001",
            "FIND-002",
            "FIND-003",
            "FIND-004",
        ],
    )

    # Semantic:
    # (100 + 50 + 0 + 25) / 4 = 43.75
    #
    # Overall:
    # 43.75 * 0.50 + 100 * 0.20
    # + 100 * 0.20 + 100 * 0.10
    # = 71.875 -> 71.88

    assert result.overall_score == 71.88
    assert result.grade == "C"

    print("PASS: Mixed semantic classifications")


def test_semantic_timeout():

    audit = make_audit(
        semantic_status="timeout"
    )

    result = RCAQualityScorer().score(
        grounding_audit=audit,
        evidence_validation=valid_evidence(),
        confirmed_finding_ids=["FIND-001"],
    )

    assert result.status == "not_assessed"
    assert result.overall_score is None

    print("PASS: Semantic timeout handled")


def test_invalid_evidence():

    result = RCAQualityScorer().score(
        grounding_audit=make_audit(),
        evidence_validation={
            "is_valid": False,
            "errors": ["Unknown evidence ID"],
            "warnings": [],
        },
        confirmed_finding_ids=["FIND-001"],
    )

    assert result.status == "not_assessed"
    assert result.overall_score is None

    print("PASS: Invalid evidence prevents scoring")


def test_missing_finding():

    audit = make_audit(
        classifications=["supported"]
    )

    result = RCAQualityScorer().score(
        grounding_audit=audit,
        evidence_validation=valid_evidence(),
        confirmed_finding_ids=[
            "FIND-001",
            "FIND-002",
        ],
    )

    assert result.status == "not_assessed"

    print("PASS: Missing finding prevents scoring")


def test_no_confirmed_findings():

    result = RCAQualityScorer().score(
        grounding_audit=make_audit(
            classifications=[]
        ),
        evidence_validation=valid_evidence(),
        confirmed_finding_ids=[],
    )

    assert result.status == "not_assessed"

    print("PASS: No confirmed findings handled")


def test_duplicate_semantic_finding():

    audit = make_audit()

    audit["semantic"]["evaluations"].append(
        dict(audit["semantic"]["evaluations"][0])
    )

    result = RCAQualityScorer().score(
        grounding_audit=audit,
        evidence_validation=valid_evidence(),
        confirmed_finding_ids=["FIND-001"],
    )

    assert result.status == "not_assessed"

    print("PASS: Duplicate semantic finding rejected")


def main():

    test_perfect_score()
    test_deterministic_warning()
    test_mixed_semantic_classifications()
    test_semantic_timeout()
    test_invalid_evidence()
    test_missing_finding()
    test_no_confirmed_findings()
    test_duplicate_semantic_finding()

    print("\nAll RCA quality scoring tests passed.")


if __name__ == "__main__":
    main() 