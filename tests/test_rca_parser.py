from datetime import datetime, timezone

from app.rca.models import RCAAnalysis
from app.rca.parser import build_rca_report
from app.rca.evidence_store import EvidenceStore

def main():
    analysis = RCAAnalysis(
        title="Checkout Email Timeout Investigation",
        services_investigated=["checkout", "email"],
        observations=[],
        confirmed_findings=[],
        hypotheses=[],
        limitations=[
            "No distributed tracing data available"
        ],
        recommended_next_steps=[
            "Inspect checkout-to-email request latency"
        ],
    )

    evidence_store = EvidenceStore()

    report = build_rca_report(
        analysis=analysis,
        evidence_store=evidence_store,
        started_at=datetime.now(timezone.utc),
        completion_reason="test_completed"
    )

    assert report.title == analysis.title
    assert report.status.value == "completed"
    assert report.incident_id.startswith("INC-")
    assert report.evidence == []

    print("Structured RCA parser test passed")
    print(report.model_dump_json(indent=2))

if __name__ == "__main__":
    main()