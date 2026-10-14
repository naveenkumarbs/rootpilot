from __future__ import annotations

from dataclasses import dataclass 
from datetime import datetime, timezone 
from typing import Any 

@dataclass
class CachedLogQuery:
    arguments: dict[str, Any]
    results: list[dict[str, Any]]
    complete: bool

class QueryCoverage:
    """
    Determines whether a previous OpenSearch query can safely
    satisfy a new absolute-time query.

    Conservative by design:
    - Only absolute-time queryis
    - Same service
    - Compatible severity filters
    - Fully covered time window
    - Previous result must not be truncated
    """

    @staticmethod
    def _parse_time(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("Timezone-aware timestamp required")
        return parsed.astimezone(timezone.utc)

    @classmethod
    def _window(cls, arguments: dict[str, Any]):
        start = arguments.get("start_time")
        end = arguments.get("end_time")

        if not start or not end:
            return None

        try:
            start_dt = cls._parse_time(start)
            end_dt = cls._parse_time(end)
        except (ValueError, TypeError, AttributeError):
            return None 

        if start_dt >= end_dt:
            return None 

        return start_dt, end_dt 

    @staticmethod
    def _severity_compatible(
        cached: dict[str, Any],
        requested: dict[str, Any],
    ) -> bool:
        cached_severity = cached.get("severity")
        requested_severity = requested.get("severity")

        # Cached query included all severities
        if cached_severity is None:
            return True 

        # Cached query included only one severity.
        return (
            requested_severity is not None
            and str(cached_severity).upper() == str(requested_severity).upper()
        )

    @classmethod
    def can_reuse(
        cls,
        cached: CachedLogQuery,
        requested: dict[str, Any],
    ) -> bool:

        if not cached.complete:
            return False 

        if cached.arguments.get("service_name") != requested.get("service_name"):
            return False 

        if not cls._severity_compatible(cached.arguments, requested):
            return False

        cached_window = cls._window(cached.arguments)
        requested_window = cls._window(requested)

        if cached_window is None or requested_window is None:
            return False

        cached_start, cached_end = cached_window 
        requested_start, requested_end = requested_window

        return(
            cached_start <= requested_start
            and requested_end <= cached_end 
        )

    @classmethod
    def filter_results(
        cls,
        cached: CachedLogQuery,
        requested: dict[str, Any],
    ) -> list[dict[str, Any]]:

        if not cls.can_reuse(cached, requested):
            raise ValueError("Cached query does not cover request")

        requested_start, requested_end = cls._window(requested)
        severity = requested.get("severity")
        filtered = [] 

        for log in cached.results:
            timestamp = log.get("timestamp")
            if timestamp is None:
                raise ValueError(
                    "Cannot filter cached logs without timestamps"
                )

            log_time = cls._parse_time(timestamp)
            if not (requested_start <= log_time <= requested_end):
                continue 
            if severity is not None:
                if (str(log.get("severity", "")).upper() != str(severity).upper()):
                    continue 

            filtered.append(log)

        limit = int(requested.get("limit", 20))

        # Preserve newest-first ordering, matching OpenSearch
        filtered.sort(
            key=lambda log: cls._parse_time(log["timestamp"]),
            reverse=True
        )

        return filtered[:limit]