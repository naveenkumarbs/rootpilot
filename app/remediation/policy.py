from dataclasses import dataclass 

from app.remediation.models import RemediationPlan

ALLOWED_ACTIONS = {
    "inspect_service_health",
    "inspect_service_metrics",
    "restart_service",
    "scale_service",
}

@dataclass
class PolicyDecision:
    allowed: bool
    reason: str 


class RemediationPolicy:

    def validate(
        self,
        plan: RemediationPlan,
        valid_evidence_ids: set[str] | None = None,
        allowed_services: set[str] | None = None,
    ) -> PolicyDecision:

        # Fail closed if trusted context is unavailable.
        if valid_evidence_ids is None or allowed_services is None:
            return PolicyDecision(
                allowed=False,
                reason="Trusted evidence or service context missing.",
            )

        if not plan.actions:
            return PolicyDecision(
                allowed=False,
                reason="No remediation actions proposed.",
            )

        for action in plan.actions:
            if action.action_type not in ALLOWED_ACTIONS:
                return PolicyDecision(
                    allowed=False,
                    reason=f"Unsupported action: {action.action_type}",
                )

            if action.target_service not in allowed_services:
                return PolicyDecision(
                    allowed=False,
                    reason=(
                        f"Unauthorized target service: "
                        f"{action.target_service}"
                    ),
                )

            if not action.supporting_evidence_ids:
                return PolicyDecision(
                    allowed=False,
                    reason="Action lacks supporting evidence.",
                )

            unknown_ids = (
                set(action.supporting_evidence_ids)
                - set(valid_evidence_ids)
            )

            if unknown_ids:
                return PolicyDecision(
                    allowed=False,
                    reason=f"Unknown evidence IDs: {sorted(unknown_ids)}",
                )

        return PolicyDecision(
            allowed=True,
            reason="Plan passed preliminary policy validation.",
        )
