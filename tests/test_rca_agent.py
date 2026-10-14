import asyncio
import json

from app.agents.rca_agent import RCAAgent

async def main():
    agent = RCAAgent()
    result = await agent.investigate(
        "Investigate the checkout service timeout that occurred on "
        "2026-10-13 at approximately 14:01:18 UTC. "
        "Checkout failed while calling the email service. "
        "Correlate checkout and email service logs around the incident "
        "timestamp and identify the most likely root cause."
    )

    print("\n===== EVIDENCE VALIDATION =====")

    validation = result.get("validation")
    print(json.dumps(validation, indent=2))
    
    print("\n===== GROUNDING AUDIT =====")
    audit = result.get("grounding_audit", {})
    print(json.dumps(audit,indent=2, default=str))

    assert validation is not None, (
        "RCAAgent did not return validation metadata."
    )
    
    assert validation["is_valid"] is True
    assert validation["errors"] == []

    assert "grounding_audit" in result
    assert audit["status"] in {
        "completed",
        "partial",
    }

    assert audit["deterministic"] is not None
    semantic_status = audit["semantic"]["status"]

    assert semantic_status in {
        "completed",
        "not_applicable",
        "timedout",
        "failed",
    }

    if semantic_status == "completed":
        expected_finding_ids = {
            finding["finding_id"] for finding in result["rca_report"]["confirmed_findings"]
        }

        actual_finding_ids = {
            item["finding_id"] for item in audit["semantic"]["evaluations"]
        }

        assert actual_finding_ids == expected_finding_ids

    print("PASS: Grounding audit attached to RCA result")

    if result.get("rca_report"):
        print("\n===== STRUCTURED RCA REPORT =====")
        print(
            json.dumps(
                result["rca_report"],
                indent=2
            )
        )
    print("\nTool History:")

    for tool in result["tool_history"]:
        print(
            f"Iteration {tool['iteration']}: "
            f"{tool['tool']}"
            f"{tool['arguments']}"
            f"[{tool['status']}]"
        )

    print ("\nToken Usage:")

    for key, value in result["token_usage"].items():
        print(f"{key}: {value}")

    print("\nRCA Report:")
    print(result["answer"])

    print("\n===== EVIDENCE SUMMARY =====")
    print("Evidence count:", result["evidence_count"])

    for evidence in result["evidence"][:10]:
        print(
            evidence["evidence_id"],
            evidence["source"],
            evidence["summary"][:120],
        )


if __name__ == "__main__":
    asyncio.run(main())