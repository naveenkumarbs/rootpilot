import json 

from langchain_core.messages import HumanMessage, SystemMessage

from app.remediation.verification_models import VerificationReport

class RemediationVerificationAgent:
    def __init__(self, llm):
        self.llm = llm.with_structured_output(
            VerificationReport,
            method="json_schema",
        )

    async def verify(
            self, 
            remediation_plan: dict,
            execution_status: str, 
    ) -> VerificationReport:

        response = await self.llm.ainvoke([
            SystemMessage(
                content=(
                    "You are RootPilot's Remediation Verification Agent. "
                    "Evaluate the supplied remediation execution record. "
                    "The executor is a simulator and does not modify "
                    "production infrastructure. "
                    "Never claim production recovery is verified. "
                    "Distinguish simulated execution from real recovery. "
                    "Recommend how to verify recovery using actual telemetry."
                )
            ),

            HumanMessage(
                content=json.dumps({
                    "remediation_plan": remediation_plan,
                    "execution_status": execution_status,
                })
            ),
        ])

        # Enforce the simulator's trust boundary in Python
        report = VerificationReport.model_validate(response)

        if execution_status == "simulated":
            report.verification_status = "simulated_only"
        elif execution_status == "rejected":
            report.verification_status = "not_executed"
        else:
            report.verification_status = "verification_failed"

        report.production_recovery_verified = False 

        return report