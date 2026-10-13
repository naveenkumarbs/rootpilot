from datetime import datetime, timezone
from uuid import uuid4

from app.rca.models import (
    RCAAnalysis,
    RCAReport,
    InvestigationStatus
)

from app.rca.evidence_store import EvidenceStore

def build_rca_report(
        analysis: RCAAnalysis,
        evidence_store: EvidenceStore,
        started_at: datetime,
        completion_reason: str,
        status: InvestigationStatus = InvestigationStatus.COMPLETED,
) -> RCAReport:
    """
    Build the final RCAReport using:
        - LLM-generated analysis
        - Application-generated metadata
        - EvidenceStore records
    """

    finised_at = datetime.now(timezone.utc)
    incident_id = f"INC-{uuid4().hex[:12].upper()}"

    return RCAReport(
        incident_id=incident_id,
        title=analysis.title,
        status=status,
        completion_reason=completion_reason,
        started_at=started_at,
        finished_at=finised_at,
        services_investigated=analysis.services_investigated,
        evidence=evidence_store.list_all(),
        observations=analysis.observations,
        confirmed_findings=analysis.confirmed_findings,
        hypotheses=analysis.hypotheses,
        limitations=analysis.limitations,
        recommended_next_steps=analysis.recommended_next_steps
    )