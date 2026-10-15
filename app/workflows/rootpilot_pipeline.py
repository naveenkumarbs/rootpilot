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

def build_rootpilot_pipeline(
        rca_agent: RCAAgent | None = None,
        remediation_agent=None,
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
    builder.add_node("validate_policy", validate_policy)
    builder.add_node("request_approval", request_approval)
    builder.add_node("simulate_execution", simulate_execution)
    builder.add_node("reject_execution", reject_execution)

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

    builder.add_edge("simulate_execution", END)
    builder.add_edge("reject_execution", END)

    return builder.compile(checkpointer=InMemorySaver())
