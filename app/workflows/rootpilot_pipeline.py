from typing import Any, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from app.agents.rca_agent import RCAAgent
from app.workflows.rca_workflow import (
    prepare_incident,
    create_rca_node,
    store_rca_result,
    create_remediation_node,
)
from app.workflows.approval_workflow import (
    validate_policy,
    route_policy,
    request_approval,
    route_approval,
    simulate_execution,
    reject_execution,
)

from app.remediation.models import RemediationPlan
from app.remediation.policy import RemediationPolicy

def create_policy_node(
        allowed_services: set[str],
):
    def validate_remediation_policy(state:RootPilotPipelineState) -> dict:
        plan = RemediationPlan.model_validate(state["remediation_plan"])

        # The report must be producted by the enforced RCA pipeline.
        # Adjust this extraction to the actual report schema.
        report = state.get("rca_report", {})
        evidence_ids = {
            evidence_id
            for finding in report.get("confirmed_findings", [])
            for evidence_id in finding.get("evidence_ids", [])
        }

        decision = RemediationPolicy().validate(
            plan=plan,
            valid_evidence_ids=evidence_ids,
            allowed_services=allowed_services,
        )

        print("[LangGraph] Policy:", decision.reason)

        return {
            "policy_allowed": decision.allowed,
            "policy_reason": decision.reason,
        }
    return validate_remediation_policy


class RootPilotPipelineState(TypedDict, total=False):
    incident: str 
    prepared_incident: str
    rca_result: dict[str, Any]
    rca_report: dict[str, Any]
    status: str 
    completion_reason: str | None 
    remediation_plan: dict[str, Any]
    policy_allowed: bool 
    policy_reason: str 
    approved: bool 
    execution_status: str
    verification_report: dict[str, Any] 

def create_verification_node(verification_agent):
    async def verify_remediation(state: RootPilotPipelineState) -> dict:
        print("[LangGraph] Starting Verification Agent")
        report = await verification_agent.verify(
            remediation_plan=state["remediation_plan"],
            execution_status=state["execution_status"],
        )

        return {"verification_report": report.model_dump(mode="json")}
    return verify_remediation

def build_rootpilot_pipeline(
        rca_agent: RCAAgent | None = None,
        remediation_agent=None,
        verification_agent=None,
        allowed_services: set[str] | None = None,
):
    if rca_agent is None:
        rca_agent = RCAAgent()

    if remediation_agent is None:
        raise ValueError(
            "A remediation planning agent must be provided."
        )

    builder = StateGraph(RootPilotPipelineState)

    builder.add_node("prepare_incident", prepare_incident)
    builder.add_node("rca_agent", create_rca_node(rca_agent))
    builder.add_node("store_rca_result", store_rca_result)
    builder.add_node("remediation_agent", create_remediation_node(remediation_agent))

    builder.add_node("validate_policy", create_policy_node(allowed_services=allowed_services or set())),
    
    builder.add_node("request_approval", request_approval)
    builder.add_node("simulate_execution", simulate_execution)
    builder.add_node("reject_execution", reject_execution)
    if verification_agent is not None:
        builder.add_node(
            "verification_agent",
            create_verification_node(verification_agent)
        )

    builder.add_edge(START, "prepare_incident")
    builder.add_edge("prepare_incident", "rca_agent")
    builder.add_edge("rca_agent", "store_rca_result")
    builder.add_edge("store_rca_result", "remediation_agent")
    builder.add_edge("remediation_agent", "validate_policy")

    builder.add_conditional_edges(
        "validate_policy",
        route_policy,
        {
            "approval": "request_approval",
            "rejected": "reject_execution",
        },
    )

    builder.add_conditional_edges(
        "request_approval",
        route_approval,
        {
            "approved": "simulate_execution",
            "rejected": "reject_execution",
        },
    )

    if verification_agent is not None:
        builder.add_edge(
            "simulate_execution",
            "verification_agent",
        )
        builder.add_edge(
            "reject_execution",
            "verification_agent"
        )
        builder.add_edge("verification_agent", END)
    else:
        builder.add_edge("simulate_execution", END)
        builder.add_edge("reject_execution", END)
    
    return builder.compile(checkpointer=InMemorySaver())
