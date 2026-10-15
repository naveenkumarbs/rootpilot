import asyncio
import json

from app.workflows.rca_workflow import build_rca_workflow

async def main():
    graph = build_rca_workflow()
    result = await graph.ainvoke({
        "incident": (
            "Investigate the checkout service timeout on "
            "2026-10-13 at approximately 14:01:18 UTC. "
            "Checkout failed while calling the email service. "
            "Correlate checkout and email logs."
        )
    })

    print("\n===== WORKFLOW RESULT =====")
    print("Status:", result["status"])
    print("Completion reason:", result["completion_reason"])

    report = result["rca_report"]

    if report:
        print(json.dumps(report, indent=2))
    else:
        print("No structured RCA report was produced.")

    assert "rca_result" in result
    assert result["status"] == result["rca_result"]["status"]

    print("\nPASS: LangGraph RCA workflow completed")


if __name__ == "__main__":
    asyncio.run(main())