from dataclasses import dataclass, field

from app.rca.models import RCAAnalysis
from app.rca.evidence_store import EvidenceStore

@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class EvidenceValidator:
    """
    Validates evidence references in LLM-generated RCA analysis.

    EvidenceStore is the source of truth for valid evidence IDs.
    
    This validtor checks reference integrity, not whether
    an evidence record semantically supports a statement.
    """

    def validate(
            self,
            analysis: RCAAnalysis,
            evidence_store: EvidenceStore,
    ) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        def check_references(
                record_type: str,
                record_id: str,
                evidence_ids: list[str],
        ) -> None:
            for evidence_id in evidence_ids:
                if evidence_store.get(evidence_id) is None:
                    errors.append(
                        f"{record_type} '{record_id}' references"
                        f"unknown evidence ID ' {evidence_id}"
                    )

        # 1. Validate observations
        for observation in analysis.observations:
            check_references(
                record_type="Observation",
                record_id=observation.observation_id,
                evidence_ids=observation.evidence_ids,
            )

        # 2. validate confirmed findings
        for finding in analysis.confirmed_findings:
            check_references(
                record_type="Finding",
                record_id=finding.finding_id,
                evidence_ids=finding.evidence_ids,
            )

        # 3. Validate supporting and contradicting evidence
        for hypothesis in analysis.hypotheses:
            check_references(
                record_type="Hypothesis (supporting)",
                record_id=hypothesis.hypothesis_id,
                evidence_ids=hypothesis.supporting_evidence_ids
            )

            check_references(
                record_type="Hypothesis (contradicting)",
                record_id=hypothesis.hypothesis_id,
                evidence_ids=hypothesis.contradicting_evidence_ids
            )

        # 4. Generate informational warnings
        if evidence_store.count() == 0:
            warnings.append(
                "No evidence was collected during te investingation."
            )

        if not analysis.confirmed_findings:
            warnings.append(
                "No confirmed findings are generated."
            )

        return ValidationResult(
            is_valid=(len(errors) == 0),
            errors=errors,
            warnings=warnings
        )