import asyncio

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

    print("\n===== RCA Result =====")
    print("Status:", result["status"])
    print("Iterations:", result["iterations"])
    print("Tool calls:", result["tool_calls_executed"])
    print("Duration:", result["duration_seconds"], "seconds")

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


if __name__ == "__main__":
    asyncio.run(main())