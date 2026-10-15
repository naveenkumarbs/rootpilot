from typing import Any, TypedDict
from langgraph.graph import StateGraph, START, END 

from app.agents.rca_agent import RCAAgent

class RCAWorkflowState(TypedDict, total=False):
    incident: str
    prepared_incident: str
    rca_result: dict[str, Any]
    rca_report: dict[str, Any]
    status: str 
    completion_reason: str | None 
    remediation_plan: dict[str, Any]

def prepare_incident(state: RCAWorkflowState) -> dict:
    incident = state["incident"].strip()

    if not incident:
        raise ValueError("Incident description cannot be empty.")

    print("[LangGraph] Incident prepared")
    return {"prepared_incident": incident}

def create_rca_node(agent: RCAAgent):
    async def investigate_incident(
            state: RCAWorkflowState,
    ) -> dict:
        print("[LangGraph] Starting RCA Agent")
        result = await agent.investigate(state["prepared_incident"])

        return {"rca_result": result}

    return investigate_incident 

def store_rca_result(state: RCAWorkflowState) -> dict: 
    result = state["rca_result"]

    print("[LangGraph] Processing RCA result")

    return{
        # Use the enforced report, not original_rca_report.
        "rca_report": result.get("rca_report", {}),
        "status": result.get("status", "unknown"),
        "completion_reason": result.get("completion_reason")
    }

def create_remediation_node(remediation_agent):
    async def plan_remediation(state: RCAWorkflowState) -> dict:
        report = state.get("rca_report", {})
        if not report:
            return {"remediation_plan": {}}

        plan = await remediation_agent.plan(report)

        return { "remediation_plan": plan.model_dump(mode="json")}

    return plan_remediation

    
def build_rca_workflow(agent: RCAAgent | None = None, remediation_agent=None):
    if agent is None:
        agent = RCAAgent()

    builder = StateGraph(RCAWorkflowState)

    builder.add_node("prepare_incident", prepare_incident)
    builder.add_node("rca_agent", create_rca_node(agent))
    builder.add_node("store_rca_result", store_rca_result)

    builder.add_edge(START, "prepare_incident")
    builder.add_edge("prepare_incident", "rca_agent")
    builder.add_edge("rca_agent", "store_rca_result")

    if remediation_agent is not None:
        builder.add_node(
            "remediation_agent",
            create_remediation_node(remediation_agent),
        )
        builder.add_edge("store_rca_result", "remediation_agent")
        builder.add_edge("remediation_agent", END)
    else:
        builder.add_edge("store_rca_result", END)
        
    return builder.compile()

