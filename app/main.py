import httpx 

from fastapi import FastAPI
from fastapi import HTTPException, Query

from dataclasses import asdict 

from app.config.settings import settings
from app.telemetry.prometheus_client import PrometheusClient
from app.detection.anomaly_detector import AnomalyDetector
from app.telemetry.opensearch_client import OpenSearchClient

app = FastAPI(
    title=settings.app_name,
    version="0.1.0"
)

prometheus = PrometheusClient()
anomaly_detector = AnomalyDetector()
opensearch = OpenSearchClient()

@app.get("/telemetry/metrics/query")
async def query_metrics(query: str):
    try:
        result = await prometheus.query(query)

        return {
            "query": query,
            "result": result
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )

@app.get("/health")
async def health():
    return {
        "status": "UP",
        "application": settings.app_name,
        "environment": settings.app_env
    }

@app.get("/detection/memory/{container_name}")
async def detect_memory_anomaly(
    container_name: str, 
    threshold_mb:float = Query(default=800, gt=0),

):
    """
    Check a container's memory usage against a threshold
    """

    # Vaidate Container Name

    # Convert MiB to bytes
    threshold_bytes = threshold_mb * 1024 * 1024

    # Query Prometheus
    promql = (
        'container_memory_usage_total_bytes'
        f'{{container_name="{container_name}"}}'
    )

    try:
        results = await prometheus.query(promql)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrievemetrics from Prometheus",
        )

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No memory metrics found for {container_name}",
        )

    try:
        memory_bytes = float(results[0]["value"][1])
    except (KeyError, IndexError, TypeError, ValueError):
        raise HTTPException(
            status_code=502,
            detail="Unexpected metric response from Prometheus",
        )

    anomaly = anomaly_detector.detect_high_memory(
        container_name=container_name,
        memory_bytes=memory_bytes,
        threshold_bytes=threshold_bytes
    )

    return {
        "container": container_name,
        "memory_mib": round(memory_bytes / (1024 * 1024), 2),
        "threshold_mib": threshold_mb,
        "anomaly_detected": anomaly is not None,
        "anomaly": asdict(anomaly) if anomaly else None,
    }

@app.get("/telemetry/logs/{service_name}")
async def get_service_logs(
    service_name: str,
    minutes: int = Query(default=15, ge=1, le=1440),
    limit: int = Query(default=20, ge=1, le=100),
    severity: str | None = None,
):
    try:
        logs = await opensearch.search_logs(
            service_name=service_name,
            minutes=minutes,
            severity=severity,
            limit=limit,
        )

        return {
            "service_name": service_name,
            "count": len(logs),
            "logs": logs,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve logs from OpenSearch"
        )
    
