from app.telemetry.opensearch_client import OpenSearchClient

async def search_service_logs(
        service_name:str,
        minutes: int=15,
        severity: str | None=None,
        limit: int=20
):
    """
    Search logs for a specific service.
    This is a read-only tool
    """

    if not service_name or len(service_name)>100:
        raise ValueError("Invalid service name")
    if not 1 <= minutes <= 60:
        raise ValueError("minutes must be between 1 and 60")
    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")

    client = OpenSearchClient()

    logs = await client.search_logs(
        service_name=service_name,
        minutes=minutes,
        severity=severity,
        limit=limit
    )

    return logs