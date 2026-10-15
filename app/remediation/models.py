from typing import Literal

from pydantic import BaseModel, Field 

class RemediationAction(BaseModel):
    action_type: Literal[
        "inspect_service_health",
        "inspect_service_metrics",
        "restart_service",
        "scale_service",
    ]

    target_service:str 
    rationale: str 
    risk_level: Literal["low", "medium", "high"]
    supporting_evidence_ids: list[str] = Field(default_factory=list)

class RemediationPlan(BaseModel):
    incident_summary: str 
    actions: list[RemediationAction] = Field(default_factory=list)
