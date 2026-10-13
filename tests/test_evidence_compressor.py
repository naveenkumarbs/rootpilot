from datetime import datetime, timezone, timedelta

from app.rca.evidence_compressor import EvidenceCompressor
from app.rca.models import Evidence, EvidenceType


def make_evidence(
    evidence_id: str,
    message: str,
    severity: str,
    seconds: int = 0,
    service: str = "email",
) -> Evidence:

    timestamp = datetime(
        2026, 10, 13, 14, 0, 0,
        tzinfo=timezone.utc,
    ) + timedelta(seconds=seconds)

    return Evidence(
        evidence_id=evidence_id,
        evidence_type=EvidenceType.LOG,
        source=service,
        severity=severity,
        observed_at=timestamp,
        collected_at=datetime.now(timezone.utc),
        tool_name="search_service_logs",
        tool_arguments={},
        summary=message,
    )


def test_repetitive_info_logs():

    evidence = [
        make_evidence(
            f"EV-{i:04d}",
            "Order confirmation email sent",
            "INFO",
            seconds=i,
        )
        for i in range(1, 21)
    ]

    compressed = EvidenceCompressor().compress(evidence)

    assert len(compressed) == 1

    group = compressed[0]

    assert group["type"] == "compressed_log_group"
    assert group["occurrences"] == 20
    assert len(group["evidence_ids"]) == 20

    print("PASS: Repetitive INFO logs compressed")


def test_error_logs_preserved():

    evidence = [
        make_evidence(
            "EV-0001",
            "Connection timeout",
            "ERROR",
        ),
        make_evidence(
            "EV-0002",
            "Connection timeout",
            "ERROR",
        ),
    ]

    compressed = EvidenceCompressor().compress(evidence)

    assert len(compressed) == 2

    assert all(
        item["type"] == "individual_evidence"
        for item in compressed
    )

    print("PASS: ERROR logs preserved")


def test_warn_logs_preserved():

    evidence = [
        make_evidence(
            "EV-0001",
            "Slow downstream request",
            "WARN",
        ),
        make_evidence(
            "EV-0002",
            "Slow downstream request",
            "WARN",
        ),
    ]

    compressed = EvidenceCompressor().compress(evidence)

    assert len(compressed) == 2

    print("PASS: WARN logs preserved")


def test_different_messages_not_grouped():

    evidence = [
        make_evidence(
            "EV-0001",
            "Order confirmation email sent",
            "INFO",
        ),
        make_evidence(
            "EV-0002",
            "Payment completed",
            "INFO",
        ),
    ]

    compressed = EvidenceCompressor().compress(evidence)

    assert len(compressed) == 2

    print("PASS: Different messages remain separate")


def test_original_evidence_unchanged():

    evidence = [
        make_evidence(
            "EV-0001",
            "Order confirmation email sent",
            "INFO",
        ),
        make_evidence(
            "EV-0002",
            "Order confirmation email sent",
            "INFO",
        ),
    ]

    original_ids = [
        item.evidence_id
        for item in evidence
    ]

    EvidenceCompressor().compress(evidence)

    assert [
        item.evidence_id
        for item in evidence
    ] == original_ids

    print("PASS: Original evidence unchanged")


def main():

    test_repetitive_info_logs()
    test_error_logs_preserved()
    test_warn_logs_preserved()
    test_different_messages_not_grouped()
    test_original_evidence_unchanged()

    print("\nAll EvidenceCompressor tests passed.")


if __name__ == "__main__":
    main()