import httpx
import json 

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
    ) -> list[dict]:
        if not service_name or len(service_name) > 100:
            raise ValueError("Invalid service name")
        if not 1 <= minutes <= 1440:
            raise ValueError("minutes must be between 1 and 1440")
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
                    "@timestamp": {
                        "gte": f"now-{minutes}m",
                        "lte": "now"
                    }
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
    