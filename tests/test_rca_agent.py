import asyncio
import json

from app.agents.rca_agent import RCAAgent

async def main():
    agent = RCAAgent()
    result = await agent.investigate(
        """
        Investigate recent checkout errors and timeouts.

        The service identifier in OpenSearch is exactly 'checkout'.

        Start by retrieving ERROR and WARN logs for checkout.
        Investigate downstream dependencies when evidence suggests they may be involved.

        Do not repeat identical searches.

        Produce an RCA report based only on retrieved evidence.
        """
    )

    print("\n===== EVIDENCE VALIDATION =====")

    validation = result.get("validation")

    assert validation is not None, (
        "RCAAgent did not return validation metadata."
    )

    print(json.dumps(validation, indent=2))

    assert validation["is_valid"] is True
    assert validation["errors"] == []

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