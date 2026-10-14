from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field 

class QualityDimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    semantic_grounding: float = Field(ge=0, le=100)
    evidence_integrity: float = Field(ge=0, le=100)
    deterministic_grounding: float = Field(ge=0, le=100)
    evaluation_completeness: float = Field(ge=0, le=100)

class QualityAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["assessed","not_assessed"]
    overall_score: float | None = Field(default=None, ge=0, le=100)
    grade: str | None = None
    dimensions: QualityDimensions | None = None 
    findings_assessed: int = Field(default=0, ge=0)
    warnings: list[str] = Field(default_factory=list)
    reason: str | None = None 

class RCAQualityScorer:
    WEIGHTS = {
        "semantic_grounding": 0.50,
        "evidence_integrity": 0.20,
        "deterministic_grounding": 0.20,
        "evaluation_completeness": 0.10,
    }

    SEMANTIC_SCORES = {
        "supported": 100.0,
        "partially_supported": 50.0,
        "insufficient_evidence": 25.0,
        "unsupported": 0.0,
    }

    ISSUE_PENALTIES = {
        "warning": 25.0,
        "error": 50.0,
    }

    @staticmethod 
    def _grade(score: float) -> str:
        if score >= 90:
            return "A"
        if score >=80:
            return "B"
        if score >=70:
            return "C"
        if score >=60:
            return "D"
        return "F"

    @staticmethod
    def _not_assessed(reason: str) -> QualityAssessment:
        return QualityAssessment(
            status="not_assessed",
            overall_score=None,
            grade=None,
            dimensions=None, 
            findings_assessed=0,
            warnings=[],
            reason=reason,
        )

    def score(
            self,
            grounding_audit: dict[str, Any],
            evidence_validation: dict[str, Any],
            confirmed_finding_ids: list[str],
    ) -> QualityAssessment:

        expected_ids = set(confirmed_finding_ids)

        # Quality cannot be assessed if there are no confirmed findings.
        if not expected_ids:
            return self._not_assessed(
                "No confirm findings are available for scoring."
            )

        # Duplicate finding IDs make asessment ambiguous.
        if len(expected_ids) != len(confirmed_finding_ids):
            return self._not_assessed(
                "Duplicate confirmed finding IDs detected."
            )

        # Evidence integrity is a prerequisite
        if evidence_validation.get("is_valid") is not True:
            return self._not_assessed(
                "Evidence reference validation did not pass."
            )

        semantic = grounding_audit.get("semantic", {})

        if semantic.get("status") != "completed":
            return self._not_assessed(
                "Semantic grounding evaluation is unavailable."
            )

        evaluations = semantic.get("evaluations",[])
        if not isinstance(evaluations, list):
            return self._not_assessed(
                "Semantic evaluation results have an invalid format."
            )

        evaluated_ids = [
            item.get("finding_id") for item in evaluations if isinstance(item, dict)
        ]

        if len(evaluated_ids) != len(evaluations):
            return self._not_assessed(
                "Semantic evaluation cntains invalid entries."
            )

        if len(evaluated_ids) != len(set(evaluated_ids)):
            return self._not_assessed(
                "Semantic evaluation contains duplicate finding IDs."
            )

        if set(evaluated_ids) != expected_ids:
            return self._not_assessed(
                "Semantic evaluation does not cover exactly "
                "the confirmed findings"
            )

        semantic_values = []
        warnings = []

        for item in evaluations:
            classification = item.get("classification")
            if classification not in self.SEMANTIC_SCORES:
                return self._not_assessed(
                    f"Unknown semantic classification: {classification}"
                )

            semantic_values.append(
                self.SEMANTIC_SCORES[classification]
            )

            if classification != "supported":
                warnings.append(
                    f"Finding {item['finding_id']} was classified "
                    f"as {classification}."
                )

        semantic_score = (sum(semantic_values)/len(semantic_values))

        # All confirmed findings have valid references
        evidence_score = 100.0

        deterministic = grounding_audit.get("deterministic")
        if not isinstance(deterministic, dict):
            return self._not_assessed(
                "Deterministic grounding evaluation is unavailable."
            )

        issues = deterministic.get("issues",[])
        if not isinstance(issues, list):
            return self._not_assessed(
                "Deterministic grounding issues have an invalid format."
            )

        # Deduplicate identical issues before applying penalties.
        unique_issues = set()

        for issue in issues:
            if not isinstance(issue, dict):
                return self._not_assessed(
                    "Invalid deterministic grounding issue."
                )

            finding_id = issue.get("finding_id")
            issue_type = issue.get("issue_type")
            severity = issue.get("severity")

            if finding_id not in expected_ids:
                return self._not_assessed(
                    "Deterministic grounding issue references "
                    "an unknown finding."
                )

            if severity not in self.ISSUE_PENALTIES:
                return self._not_assessed(
                    f"Unknown grounding issue severity: {severity}"
                )

            unique_issues.add((finding_id, issue_type, severity))
        total_penalty = sum(self.ISSUE_PENALTIES[severity] for _, _, severity in unique_issues)
        deterministic_score = max(0.0, 100.0-total_penalty)
        if unique_issues:
            warnings.append(
                f"{len(unique_issues)} deterministic grounding "
                "issue(s) were detected."
            )

        # Exact coverage is required for assessment.
        completeness_score = 100.0
        dimensions = QualityDimensions(
            semantic_grounding=round(semantic_score, 2),
            evidence_integrity=round(evidence_score, 2),
            deterministic_grounding=round(deterministic_score, 2),
            evaluation_completeness=completeness_score,
        )
        overall = sum(getattr(dimensions, name) * weight for name, weight in self.WEIGHTS.items())
        overall = round(overall, 2)

        return QualityAssessment(
            status="assessed",
            overall_score=overall,
            grade=self._grade(overall),
            dimensions=dimensions,
            findings_assessed=len(expected_ids),
            warnings=warnings,
        )
