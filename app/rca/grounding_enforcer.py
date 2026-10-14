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

    ALLOWED_CLASSIFICATIONS = {
        "supported",
        "partially_supported",
        "unsupported",
        "insufficient_evidence",
    }

    ALLOWED_SEVERITIES = {
        "warning",
        "error",
    }

    @staticmethod
    def _valid_semantic_evaluations(
        semantic: dict,
        expected_finding_ids: set[str],
    ) -> bool:
        if semantic.get("status") != "completed":
            return False

        evaluations = semantic.get("evaluations")

        if not isinstance(evaluations, list):
            return False 

        evaluated_ids = []
        for evaluation in evaluations:
            if not isinstance(evaluation, dict):
                return False 
            finding_id = evaluation.get("finding_id")
            classification = evaluation.get("classification")

            if not isinstance(finding_id, str):
                return False
            if classification not in GroundingEnforcer.ALLOWED_CLASSIFICATIONS:
                return False 
            evaluated_ids.append(finding_id)

        if len(evaluated_ids) != len(set(evaluated_ids)):
            return False 

        return set(evaluated_ids) == expected_finding_ids

    @staticmethod
    def _valid_deterministic_evaluation(
        deterministic: dict,
        expected_finding_ids: set[str],
    ) -> bool:
        if not isinstance(deterministic, dict):
            return False 
        if not isinstance(deterministic.get("is_valid"), bool):
            return False 
        
        issues = deterministic.get("issues")
        if not isinstance(issues, list):
            return False 

        for issue in issues:
            if not isinstance(issue, dict):
                return False 
            finding_id = issue.get("finding_id")
            severity = issue.get("severity")

            if finding_id not in expected_finding_ids:
                return False
            if severity not in GroundingEnforcer.ALLOWED_SEVERITIES:
                return False 
        return True 
            
    def enforce(
        self,
        analysis: RCAAnalysis,
        grounding_audit: dict[str, Any],
        evidence_validation: dict[str, Any],
    ) -> GroundingEnforcementResult:

        findings = analysis.confirmed_findings

        expected_ids = {
            finding.finding_id
            for finding in findings
        }

        semantic = grounding_audit.get("semantic")
        deterministic = grounding_audit.get("deterministic")

        semantic_valid = (
            isinstance(semantic, dict)
            and self._valid_semantic_evaluations(
                semantic,
                expected_ids,
            )
        )

        deterministic_valid = (
            isinstance(deterministic, dict)
            and self._valid_deterministic_evaluation(
                deterministic,
                expected_ids,
            )
        )

        evidence_valid = (
            evidence_validation.get("is_valid") is True
        )

        semantic_evaluations = {}

        if semantic_valid:
            semantic_evaluations = {
                item["finding_id"]: item
                for item in semantic["evaluations"]
            }

        issues_by_finding = {}

        if deterministic_valid:
            for issue in deterministic["issues"]:
                issues_by_finding.setdefault(
                    issue["finding_id"], []
                ).append(issue)

        confirmed = []
        provisional = []
        rejected = []
        decisions = []

        for finding in findings:

            finding_id = finding.finding_id

            evaluation = semantic_evaluations.get(
                finding_id, {}
            )

            classification = evaluation.get(
                "classification"
            )

            finding_issues = issues_by_finding.get(
                finding_id, []
            )

            has_error = any(
                issue["severity"] == "error"
                for issue in finding_issues
            )

            has_warning = any(
                issue["severity"] == "warning"
                for issue in finding_issues
            )

            reasons = []

            if not evidence_valid:

                decision = EnforcementDecision.REJECTED

                reasons.append(
                    "Evidence validation failed."
                )

            elif not semantic_valid:

                decision = EnforcementDecision.PROVISIONAL

                reasons.append(
                    "Semantic grounding evaluation is "
                    "missing, incomplete, or invalid."
                )

            elif not deterministic_valid:

                decision = EnforcementDecision.PROVISIONAL

                reasons.append(
                    "Deterministic grounding evaluation is "
                    "missing or invalid."
                )

            elif has_error:

                decision = EnforcementDecision.REJECTED

                reasons.append(
                    "Deterministic grounding detected "
                    "a blocking issue."
                )

            elif classification == "unsupported":

                decision = EnforcementDecision.REJECTED

                reasons.append(
                    "Semantic grounding classified "
                    "the finding as unsupported."
                )

            elif classification in {
                "partially_supported",
                "insufficient_evidence",
            }:

                decision = EnforcementDecision.PROVISIONAL

                reasons.append(
                    f"Semantic grounding classification: "
                    f"{classification}."
                )

            elif has_warning:

                decision = EnforcementDecision.PROVISIONAL

                reasons.append(
                    "Deterministic grounding warning "
                    "requires further investigation."
                )

            elif classification == "supported":

                decision = EnforcementDecision.CONFIRMED

                reasons.append(
                    "Finding passed all grounding checks."
                )

            else:

                decision = EnforcementDecision.PROVISIONAL

                reasons.append(
                    "Finding could not be safely classified."
                )

            decisions.append(
                FindingEnforcementResult(
                    finding_id=finding_id,
                    decision=decision,
                    original_statement=finding.statement,
                    reasons=reasons,
                    semantic_classification=classification,
                    deterministic_issues=[
                        issue.get("issue_type", "unknown")
                        for issue in finding_issues
                    ],
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
