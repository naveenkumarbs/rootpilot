from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

class RootPilotState(TypedDict):
    incident: str
    prepared_incident: str
    summary: str 

def prepare_incident(state: RootPilotState) -> dict:
    """Node 1: Prepare incident information."""

    incident = state["incident"].strip()

    if not incident:
        raise ValueError("Incident description cannot be empty.")

    print("[LangGraph] Preparing incident")

    return {"prepared_incident": incident}

def create_summary_node(llm):
    def generate_summary(state: RootPilotState) -> dict:
        """Node 2: Generate a preliminary incident summary."""

        print("[LangGraph] Generating summary")

        response = llm.invoke([
            SystemMessage(
                content=(
                    "You are RootPilot, an incident investigation assistant. "
                    "Summarize the incident briefly. "
                    "Distinguish observations from hypotheses. "
                    "Do not claim an unverified root cause."
                )
            ),
            HumanMessage(content=state["prepared_incident"]),
        ])

        return {"summary": response.text}

    return generate_summary

def build_rootpilot_graph(llm):
    builder = StateGraph(RootPilotState)

    builder.add_node("prepare_incident", prepare_incident)
    builder.add_node("generate_summary", create_summary_node(llm))

    builder.add_edge(START, "prepare_incident")
    builder.add_edge("prepare_incident", "generate_summary")
    builder.add_edge("generate_summary", END)

    return builder.compile()
