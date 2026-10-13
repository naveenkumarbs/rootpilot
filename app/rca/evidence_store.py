import hashlib
import json
from datetime import datetime, timezone

from app.rca.models import Evidence

class EvidenceStore:
    """
    In-memory evidence repository scoped to one RCA investigation.

    Responsibilities:
    - Assign evidence IDs
    - Deduplicate evidence
    - Preserve telemetry provenance
    - Retrieve collected evidence
    """

    def __init__(self):
        self._evidence: dict[str, Evidence] = {}
        self._fingerprints: dict[str, str] = {}

    def add_log(self, log: dict, tool_name: str, tool_arguments: dict,) -> Evidence:
        # Build a deterministic fingerprint from the log itself
        # Tool arguments are provenance, not part of log identity.
        fingerprint_payload = {
            "timestamp": log.get("timestamp"),
            "service_name": log.get("service_name"),
            "severity": log.get("severity"),
            "message": log.get("message"),
            "trace_id": log.get("trace_id"),
            "span_id": log.get("span_id"),
        }

        fingerprint = hashlib.sha256(
            json.dumps(
                fingerprint_payload,
                sort_keys=True,
                default=str,
            ).encode("utf-8")
        ).hexdigest()

        # Return the existing record if this log was already collected
        if fingerprint in self._fingerprints:
            evidence_id = self._fingerprints[fingerprint]
            return self._evidence[evidence_id]
        
        evidence_id = f"EV-{len(self._evidence) + 1:04d}"

        evidence = Evidence(
            evidence_id=evidence_id,
            evidence_type="log",
            source=log.get("service_name","unknown"),
            observed_at=log.get("timestamp"),
            collected_at=datetime.now(timezone.utc),
            tool_name=tool_name,
            tool_arguments=tool_arguments,
            summary=log.get("message",""),
            raw_reference=None,
        )

        self._evidence[evidence_id] = evidence
        self._fingerprints[fingerprint] = evidence_id

        return evidence

    def get(self, evidence_id: str) -> Evidence | None:
        return self._evidence.get(evidence_id)
    
    def list_all(self) -> list[Evidence]:
        return list(self._evidence.values())

    def count(self) -> int:
        return len(self._evidence)