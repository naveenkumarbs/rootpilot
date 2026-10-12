from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class Anomaly:
    container_name: str
    metric_name: str 
    observed_value: float 
    threshold: float 
    severity: str 
    detected_at: str 

class AnomalyDetector:
    def detect_high_memory(
            self, 
            container_name: str, 
            memory_bytes: float, 
            threshold_bytes: float
    ) -> Anomaly | None :
        
        if memory_bytes <= threshold_bytes:
            return None

        ratio = memory_bytes/threshold_bytes
        severity = "CRITICAL" if ratio >= 1.5 else "WARNING" 

        return Anomaly(
            container_name=container_name,
            metric_name="container_memory_usage_total_bytes",
            observed_value=memory_bytes,
            threshold=threshold_bytes,
            severity=severity,
            detected_at=datetime.now(timezone.utc).isoformat(),
        )

    