import httpx

from app.config.settings import settings

class PrometheusClient:
    def __init__(self):
        self.base_url = settings.prometheus_url 
    
    async def query(self, promql: str):
        """
        Execute an instant PromQL query against Prometheus
        """

        url = f"{self.base_url}/api/v1/query"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params={"query": promql},
                timeout=10.0
            )

            response.raise_for_status()

            data = response.json()

            if data.get("status") != "success":
                raise RuntimeError(
                    f"Prometheus query failed: {data}"
                )

            return data["data"]["result"]