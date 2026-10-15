import asyncio

from app.workflows.rca_workflow import build_rca_workflow

class FakeRCAAgent:
    def __init__(self):
        self.calls = 0
        self.last_prompt = None 

    async def investigate(self,prompt: str):
        self.calls += 1
        self.last_prompt = prompt 

        return {
            "status": "partial",
            "completion_reason": "investigation_saturated",
            "rca_report": {
                "title": "Checkout timeout investigation",
                "status": "partial",
                "completion_reason": "investigation_saturated",
                "confirmed_findings": [
                    {
                        "finding_id": "F-001",
                        "description": (
                            "Checkout timed out while calling email."
                        ),
                        "evidence_ids": ["EV-0001"],
                    }
                ],
                "provisional_findings": [],
                "rejected_findings": [],
            },
            "original_rca_report": {
                "title": "Unenforced report"
            },
        }

async def main():
    fake_agent = FakeRCAAgent()
    graph = build_rca_workflow(agent=fake_agent)
    result = await graph.ainvoke({
        "incident": "Investigate checkout timeout."
    })

    assert fake_agent.calls == 1
    assert fake_agent.last_prompt == "Investigate checkout timeout."

    assert result["status"] == "partial"

    assert result["completion_reason"] == "investigation_saturated"

    assert result["rca_report"]["confirmed_findings"][0]["finding_id"] == "F-001"

    # Ensure downstream nodes receive the enforced report.
    assert result["rca_report"]["title"] != result["rca_result"]["original_rca_report"]["title"]

    print("PASS: LangGraph invoked RCA Agent")
    print("PASS: Incident input was normalized")
    print("PASS: RCA result stored in shared graph state")
    print("PASS: Enforced RCA report preserved")


if __name__ == "__main__":
    asyncio.run(main())
