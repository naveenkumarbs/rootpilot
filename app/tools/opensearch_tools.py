from app.telemetry.opensearch_client import OpenSearchClient

async def search_service_logs(
        service_name:str,
        minutes: int | None = None,
        severity: str | None=None,
        limit: int=20,
        start_time: str | None=None,
        end_time: str | None=None
):
    """
    Search logs for a specific service.
    This is a read-only tool
    """

    has_start = start_time is not None
    has_end = end_time is not None

    if has_start != has_end:
        raise ValueError(
            "start_time and end_time must be provided together."
        )

    if has_start:
        if minutes is not None:
            raise ValueError(
                "Provide either minutes or start_time/end_time, not both."
            )
    else:
        if minutes is None:
            minutes = 15
        if (isinstance(minutes, bool) or not isinstance(minutes,int) or not 1<=minutes<=60):
            raise ValueError("minutes must be an integer between 1 and 60.")
        
    client = OpenSearchClient()

    logs = await client.search_logs(
        service_name=service_name,
        minutes=minutes,
        severity=severity,
        limit=limit,
        start_time=start_time,
        end_time=end_time
    )

    return logs