import asyncio

from app.tools.opensearch_tools import search_service_logs


async def main():
    logs = await search_service_logs(
        service_name="checkout",
        start_time="2026-10-13T14:00:00Z",
        end_time="2026-10-13T14:05:00Z",
        limit=20,
    )

    print(f"Logs returned: {len(logs)}")

    for log in logs:
        print(
            log.get("timestamp"),
            log.get("service"),
            log.get("severity"),
            log.get("message"),
        )

    assert isinstance(logs, list)

    print("\nAbsolute-time OpenSearch query executed successfully.")


if __name__ == "__main__":
    asyncio.run(main())