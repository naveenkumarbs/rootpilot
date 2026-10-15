from typing import TypedDict

from langgraph.graph import StateGraph, START, END 
from langgraph.types import interrupt 
from langgraph.checkpoint.memory import InMemorySaver

from app.remediation.models import RemediationPlan
from app.remediation.policy import RemediationPolicy

class ApprovalState(TypedDict, total=False):
    remediation_plan: dict 
    policy_allowed: bool
    policy_reason: str 
    approved: bool 
    execution_status: str 

def validate_policy(state: ApprovalState) -> dict:
    plan=RemediationPlan.model_validate(state["remediation_plan"])
    decision = RemediationPolicy().validate(plan)

    print("[LangGraph] Policy: ", decision.reason) 

    return {
        "policy_allowed": decision.allowed,
        "policy_reason": decision.reason,
    }

def route_policy(state: ApprovalState) -> str: 
    return "approval" if state["policy_allowed"] else "rejected" 

def request_approval(state: ApprovalState) -> dict: 
    print("[LangGraph] waiting for human approval")

    response = interrupt({
        "message": "Approve this remediation plan?",
        "remediation_plan": state["remediation_plan"],
        "policy_reason": state["policy_reason"],
    })

    # Only an explicit boolean True counts as approval
    approved = response is True 

    return {"approved": approved}

def route_approval(state: ApprovalState) -> str :
    return "approved" if state["approved"] else "rejected"

def simulate_execution(state: ApprovalState) -> dict:
    print("[LangGraph] Simulating remediation")

    for action in state["remediation_plan"]["actions"]:
        print(
            f"[SIMULATED] {action['action_type']} "
            f"on {action['target_service']}"
        )

    return {"execution_status": "simulated"}

def reject_execution(state: ApprovalState) -> dict: 
    print("[LangGraph] Remediation not executed")
    return {"execution_status": "rejected"}

def build_approval_workflow():
    builder = StateGraph(ApprovalState)

    builder.add_node("validate_policy", validate_policy)
    builder.add_node("request_approval", request_approval)
    builder.add_node("simulate_execution", simulate_execution)
    builder.add_node("reject_execution", reject_execution)

    builder.add_edge(START, "validate_policy")
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

