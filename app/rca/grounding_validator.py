from __future__ import annotations

import re 

from dataclasses import dataclass, field 

from app.rca.models import RCAAnalysis
from app.rca.evidence_store import EvidenceStore

@dataclass
class GroundingIssue:
    finding_id: str
    issue_type: str 
    severity: str
    message: str 
    evidence_ids: list[str] = field(default_factory=list)

@dataclass
class GroudingResult:
    is_valid: bool 
    issues: list[GroundingIssue] = field(default_factory=list)
    checked_findings: int = 0

class GroundingValidator:
    """
    Detects selected high-rish RCA claims that are not established by their cited evidence.

    This is a conservative heuristic validator, not a complete semantic entailment checker
    """

    OUTAGE_CLAIMS = re.compile(
        r"\b("
        r"(?:service|server|system)\s+(?:was|is)\s+"
        r"(?:down|unavailable|offline)"
        r"|complete\s+outage"
        r")\b",
        re.IGNORECASE,
    )

    RECOVERY_CLAIMS = re.compile(
        r"\b("
        r"(?:service|system)\s+(?:recovered|was restored)"
        r"|(?:issue|outage)\s+(?:was resolved|ended)"
        r")\b",
        re.IGNORECASE,
    )

    ROOT_CAUSE_CLAIMS = re.compile(
        r"\b("
        r"root cause (?:was|is)"
        r"|caused by"
        r"|due to"
        r")\b",
        re.IGNORECASE,
    )

    TIMEOUT_SIGNALS = (
        "context deadline exceeded",
        "timed out",
        "timeout",
        "deadline exceeded",
    )

    SUCCESS_SIGNALS = (
        "success",
        "completed successfully",
        "email sent",
        "request completed",
    )

    @staticmethod
    def _evidence_texts(
        evidence_ids: list[str],
        evidence_store: EvidenceStore,
    ) -> list[str]:

        texts = []

        for evidence_id in evidence_ids:
            evidence = evidence_store.get(evidence_id)
            if evidence is not None:
                texts.append(evidence.summary.lower())
        return texts 

    def validate(
        self,
        analysis: RCAAnalysis,
        evidence_store: EvidenceStore,
    ) -> GroudingResult:

        issues = []

        for finding in analysis.confirmed_findings:
            statement = finding.statement 
            statement_lower = statement.lower()

            evidence_texts = self._evidence_texts(
                finding.evidence_ids,
                evidence_store,
            )

            combined_evidence = " ".join(evidence_texts)

            # Service outage inferred from timeout alone
            if self.OUTAGE_CLAIMS.search(statement):
                only_timeout_evidence = (
                    any(
                        signal in combined_evidence
                        for signal in self.TIMEOUT_SIGNALS
                    )
                    and not any(
                        signal in combined_evidence
                        for signal in (
                            "service unavailable",
                            "service is down",
                            "connection refused",
                            "health check failed",
                        )
                    )
                )

                if only_timeout_evidence:
                    issues.append(
                        GroundingIssue(
                            finding_id = finding.finding_id,
                            issue_type = "unsupported_outage_claim",
                            severity = "error",
                            message = (
                                "A client-side timeout does not "
                                "establish that the downstream "
                                "service was unavailable."
                            ),
                            evidence_ids=finding.evidence_ids,
                        )
                    )

            # Recovery inferred from sucess logs alone.
            if self.RECOVERY_CLAIMS.search(statement):
                success_evidence = any(
                    signal in combined_evidence for signal in self.SUCCESS_SIGNALS
                )

                explicit_recovery_evidence = any(
                    signal in combined_evidence
                    for signal in (
                        "recovered",
                        "restored",
                        "health check passed",
                        "incident resoled",
                    )
                )

                if (success_evidence and not explicit_recovery_evidence):
                    issues.append(
                        GroundingIssue(
                            finding_id=finding.finding_id,
                            issue_type="unsupported_recovery_claim",
                            severity="error",
                            message=(
                                "Later successful operations do not "
                                "establish when or whether the "
                                "original incident was resolved."
                            ),
                            evidence_ids=finding.evidence_ids,
                        )
                    )

            # Root cause asserted from timeout symptoms alone.
            if self.ROOT_CAUSE_CLAIMS.search(statement):
                has_timeout = any(
                    signal in combined_evidence for signal in self.TIMEOUT_SIGNALS
                )

                if has_timeout:
                    issues.append(
                        GroundingIssue(
                            finding_id=finding.finding_id,
                            issue_type="possible_unsupported_causality",
                            severity="warning",
                            message=(
                                "A timeout is an observed sympto. "
                                "Verify that the cited evidence "
                                "supports the claimed cause."
                            ),
                            evidence_ids=finding.evidence_ids,
                        )
                    )
        return GroudingResult(
            is_valid = not any(
                issue.severity == "error" for issue in issues
            ),
            issues = issues,
            checked_findings=len(analysis.confirmed_findings),
        )
            
    