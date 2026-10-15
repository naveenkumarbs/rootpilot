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
    def validate(self, plan: RemediationPlan) -> PolicyDecision:
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

            if not action.target_service.strip():
                return PolicyDecision(
                    allowed=False,
                    reason="Target service is missing.",
                )

            if not action.supporting_evidence_ids:
                return PolicyDecision(
                    allowed=False,
                    reason="Action lacks supporting evidene.",
                )

        return PolicyDecision(
            allowed=True,
            reason="Plan passed preliminary policy validation.",
        )