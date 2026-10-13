import httpx
import json 

from datetime import datetime, timezone 

from app.config.settings import settings

class OpenSearchClient:
    def __init__(self):
        self.base_url = settings.opensearch_url.rstrip("/")
        self.index_pattern = "otel-logs-*"


    """
    . Structured OpenSearch queries instead of arbitrary search strings.
    . Time-window restrictions to limit how much historical data an agent can retrieve.
    . Result limits to control query costs and LLM context size.
    . Selected source fields to avoid returning unnecessary identifiers and host metadata.
    . Trace IDs to support future correlation with Jaeger.
    """
    async def search_logs(
            self,
            service_name: str, 
            minutes: int = 15,
            severity: str | None = None, 
            limit: int = 20,
            start_time: str | None = None,
            end_time: str | None = None,
    ) -> list[dict]:
        if not service_name or len(service_name) > 100:
            raise ValueError("Invalid service name")

        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")

        filters = [
            {
                "term": {
                    "resource.service.name.keyword": service_name
                }
            },
            {
                "range": {
                    "@timestamp": build_time_range(
                        minutes=minutes,
                        start_time=start_time,
                        end_time=end_time,
                    )
                }
            }
        ]

        if severity:
            filters.append({
                "term": {
                    "severity.text.keyword": severity.upper()
                }
            })

        query = {
            "size": limit, 
            "track_total_hits": False,
            "_source": [
                "@timestamp",
                "resource.service.name",
                "severity",
                "body",
                "traceId",
                "spanId"
            ],
            "query": {
                "bool": {
                    "filter": filters
                }
            },
            "sort": [
                {
                    "@timestamp": {
                        "order": "desc"
                    }
                }
            ]
        }

        url = f"{self.base_url}/{self.index_pattern}/_search"
        """
        print (
            "\n[DEBUG] OpenSearch request:",
            json.dumps(query, indent=2)
        )
        print ("[DEBUG] OpenSearch URL:", url)

        print("\n[DEBUG] Opensearch Query:")
        print(json.dumps(query, indent=2))
        """

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=query)
            response.raise_for_status()
            data = response.json()

        """
        print (
            "[DEBUG] OpenSearch response:",
            json.dumps(
                {
                    "timed_out": data.get("timed_out"),
                    "shards": data.get("_shards"),
                    "total_hits": data.get("hits", {}).get("total"),
                    "returned_hits": len(
                        data.get("hits", {}).get("hits", [])
                    ),
                },
                indent = 2
            )
        )
        """

        logs = []

        for hit in data.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            logs.append({
                "timestamp": source.get("@timestamp"),
                "service_name": source.get(
                    "resource", {}
                ).get("service.name"),
                "severity": source.get(
                    "severity", {}
                ).get("text"),
                "message": source.get("body"),
                "trace_id": source.get("traceId"),
                "span_id": source.get("spanId")
            })

        return logs

def build_time_range(
        minutes: int | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
) -> dict:
    """
    Construct an OpenSearch timestamp range.

    Supported modes:
    1. Relative: minutes
    2. Absolute: start_time + end_time

    Defaults to the last 15 mins when no time parameters are supplied
    """

    has_start = start_time is not None
    has_end = end_time is not None 

    # Both absolute timestamps must be supplied together
    if has_start != has_end:
        raise ValueError(
            "start_time and end_time must be provided together."
        )

    # Prevent conflicting time selection modes.
    if has_start and minutes is not None:
        raise ValueError(
            "Provide either minutes or start_time/end_time, not both"
        )

    if has_start:
        try:
            start = datetime.fromisoformat(
                start_time.replace("Z", "+00:00")
            )
            end = datetime.fromisoformat(
                end_time.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise ValueError(
                "Invalid ISO-8601 timestamp."
            ) from exc 

        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError(
                "TImestamps must include timezone information."
            )

        start = start.astimezone(timezone.utc)
        end = end.astimezone(timezone.utc) 

        if (start >= end):
            raise ValueError(
                "start_time must be earlier than end_time"
            )

        if (end-start).total_seconds() > 3600:
            raise ValueError(
                "Absolute time range cannot exceed 60 minutes."
            )

        return {
            "gte": start.isoformat(),
            "lte": end.isoformat(),
        }

    # Relative mode
    if minutes is None:
        minutes = 15

    if isinstance(minutes, bool) or not isinstance(minutes, int):
        raise ValueError("minutes must be an integer")
    if not 1 <= minutes <= 60:
        raise ValueError("minutes must be between 1 and 60")

    return {
        "gte": f"now-{minutes}m",
        "lte": "now",
    }