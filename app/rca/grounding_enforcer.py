from __future__ import annotations
from enum import Enum
from typing import Any 
from pydantic import BaseModel, ConfigDict, Field 

from app.rca.models import RCAAnalysis, Finding 

class EnforcementDecision(str, Enum):
    CONFIRMED = "confirmed"
    PROVISIONAL = "provisional"
    REJECTED = "rejected"

class FindingEnforcementResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    finding_id: str
    decision: EnforcementDecision
    original_statement: str 
    reasons: list[str] = Field(default_factory=list)
    semantic_classification: str | None = None 
    deterministic_issues: list[str] = Field(default_factory=list)

class GroundingEnforcementResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    confirmed_findings: list[Finding] = Field(default_factory=list)
    provisional_findings: list[Finding] = Field(default_factory=list)
    rejected_findings: list[Finding] = Field(default_factory=list)
    decisions: list[FindingEnforcementResult] = Field(default_factory=list)
    original_finding_count: int = 0
    confirmed_count: int = 0
    provisional_count: int = 0
    rejected_count: int = 0

class GroundingEnforcer:
    BLOCKING_SEVERITIES = {"error"}

    def enforce(
            self,
            analysis: RCAAnalysis,
            grounding_audit: dict[str, Any],
            evidence_validation: dict[str, Any],
    ) -> GroundingEnforcementResult:

        findings = analysis.confirmed_findings
        semantic = grounding_audit.get("semantic", {})
        deterministic = grounding_audit.get("deterministic", {})
        semantic_status = semantic.get("status")

        semantic_evaluations = {
            item["finding_id"]: item
            for item in semantic.get("evaluations", [])
            if isinstance(item, dict)
            and "finding_id" in item
        }

        issues_by_finding: dict[str, list[dict]] = {} 

        for issue in deterministic.get("issues", []):
            finding_id = issue.get("finding_id")
            issues_by_finding.setdefault(finding_id, []).append(issue)

        confirmed = []
        provisional = []
        rejected = []
        decisions = []

        evidence_valid = (evidence_validation.get("is_valid") is True)

        for finding in findings:
            finding_id = finding.finding_id
            evaluation = semantic_evaluations.get(finding_id, {})
            classification = evaluation.get("classification")
            finding_issues = issues_by_finding.get(finding_id, [])
            issue_types = [issue.get("issue_type", "unknown") for issue in finding_issues]

            has_blocking_issue = any(
                issue.get("severity") in self.BLOCKING_SEVERITIES 
                for issue in finding_issues
            )

            has_warning = any(
                issue.get("severity") == "warning" for issue in finding_issues
            )

            reasons = []

            # Highest priority: invalid evidence references.
            if not evidence_valid: 
                decision = EnforcementDecision.REJECTED
                reasons.append("Evidence reference validation falied.")

            # deterministic blocking violations
            elif has_blocking_issue:
                decision = EnforcementDecision.REJECTED
                reasons.append("Deterministic grounding validtion detected a blocking issue.")

            # Unsupported findings must never be confirmed
            elif (semantic_status == "completed" and classification == "unsupported"):
                decision = EnforcementDecision.REJECTED
                reasons.append("Semantic evaluator classified the finding as unsupported.")

            # Partial evidence or missing evidence
            elif (semantic_status=="completed" and classification in {"partially_supported", "insufficient_evidence"}):
                decision = EnforcementDecision.PROVISIONAL
                reasons.append(f"Semantic grounding classification: {classification}.")

            # Supported finding with deterministic warning
            elif(semantic_status=="completed" and classification=="supported" and has_warning):
                decision = EnforcementDecision.PROVISIONAL
                reasons.append("Deterministic grounding warning requires further review.")

            # Fully supported
            elif (semantic_status=="completed" and classification=="supported"):
                decision = EnforcementDecision.CONFIRMED
                reasons.append("Finding passed semantic and deterministic grounding checks.")

            # Semantic evaluation unavailable or incomplete.
            else:
                decision = EnforcementDecision.PROVISIONAL
                reasons.append("Semantic grounding evaluation is unavailable or incomplete")

            decisions.append(
                FindingEnforcementResult(
                    finding_id=finding_id,
                    decision=decision,
                    original_statement=finding.statement,
                    reasons=reasons,
                    semantic_classification=classification,
                    deterministic_issues=issue_types,
                )
            )

            if decision == EnforcementDecision.CONFIRMED:
                confirmed.append(finding)
            elif decision == EnforcementDecision.PROVISIONAL:
                provisional.append(finding)
            else:
                rejected.append(finding)

        return GroundingEnforcementResult(
            status="completed",
            confirmed_findings=confirmed,
            provisional_findings=provisional,
            rejected_findings=rejected,
            decisions=decisions,
            original_finding_count=len(findings),
            confirmed_count=len(confirmed),
            provisional_count=len(provisional),
            rejected_count=len(rejected),
        )
