import json 

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.remediation.models import RemediationPlan

class RemediationPlanningAgent:
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm.with_structured_output(
            RemediationPlan,
            method="json-schema",
        )

    async def plan(self, rca_report: dict) -> RemediationPlan:
        response = await self.llm.ainvoke([
            SystemMessage(
                content=(
                    "You are RootPilot's Remediation Planning Agent. "
                    "Recommend safe diagnostic or corrective actions "
                    "based only on the supplied RCA report. "
                    "Confirmed findings are verified observations; "
                    "hypotheses are not confirmed causes. "
                    "Do not invent evidence IDs. "
                    "Do not recommend arbitrary shell commands. "
                    "Do not execute any actions."
                )
            ),
            HumanMessage(
                content=json.dumps(rca_report, default=str)
            ),
        ])

        return RemediationPlan.model_validate(response)
    