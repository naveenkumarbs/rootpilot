from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any 

from app.rca.models import Evidence, EvidenceType

class EvidenceCompressor:
    """
    Deterministicaly compress repetitive informational log evidence.
    This class does not modify EvidenceStore or original Evidence objects.
    """

    def compress(
            self,
            evidence: list[Evidence],
    ) -> list[dict[str, Any]]:
        groups: dict[
            tuple[str, str, str],
            list[Evidence]
        ] = defaultdict(list)

        output: list[dict[str, Any]] = []

        for item in evidence:
            if not self._is_compressible(item):
                output.append(self._individual_record(item))
                continue
            severity = self._get_severity(item)

            key = (
                item.source,
                severity,
                item.summary,
            )

            groups[key].append(item)

        for (service, severity, message), items in groups.items():
            if len(items) == 1:
                output.append(
                    self._individual_record(items[0])
                )
                continue

            timestamps = [
                item.observed_at
                for item in items
                if item.observed_at is not None
            ]

            first_seen = (
                min(timestamps).isoformat()
                if timestamps else None
            )

            last_seen = (
                max(timestamps).isoformat()
                if timestamps else None
            )

            output.append({
                "type": "compressed_log_group",
                "service": service,
                "severity": severity,
                "message": message,
                "occurrences": len(items),
                "first_observed_at": first_seen,
                "last_observed_at": last_seen,
                "evidence_ids":[
                    item.evidence_id for item in items
                ],
            })

        return output

    @staticmethod
    def _get_severity(item: Evidence) -> str:
        return (item.severity or "UNKNOWN").upper()

    @classmethod
    def _is_compressible(cls, item: Evidence) -> bool:
        if item.evidence_type != EvidenceType.LOG:
            return False
        return cls._get_severity(item) == "INFO"

    @staticmethod
    def _individual_record(
        item: Evidence,
    ) -> dict[str, Any]:
        
        return {
            "type": "individual_evidence",
            "evidence_id": item.evidence_id,
            "evidence_type": item.evidence_type,
            "service": item.source,
            "severity": EvidenceCompressor._get_severity(item),
            "observed_at": (
                item.observed_at.isoformat()
                if item.observed_at else None
            ),
            "message": item.summary,
        }

