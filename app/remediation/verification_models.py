from typing import Literal 
from pydantic import BaseModel, Field

class VerificationReport(BaseModel):
    verification_status: Literal[
        "simulated_only",
        "not_executed",
        "verification_failed",
    ]

    observations: list[str] = Field(default_factory=list)

    recommended_next_steps: list[str] = Field(default_factory=list)

    production_recovery_verified: bool = False 