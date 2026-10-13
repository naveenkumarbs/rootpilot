from app.llm.models import ToolDefinition

SEARCH_SERVICE_LOGS = ToolDefinition(
    name="search_service_logs",
    description=(
        "Search OpenSearch logs for a specified service. "
        "Use minutes to retrieve recent logs. "
        "When a specific incident timestamp is known, "
        "prefer start_time and end_time to inspect logs "
        "around that incident. "
        "Do not combine minutes with start_time/end_time."
    ),
    parameters={
        "type": "object",
        "properties": {
            "service_name": {
                "type": "string",
                "description": "Name of the service to investigate."
            },
            "minutes": {
                "type": "integer",
                "minimum": 1,
                "maximum": 60,
                "description": "Relative lookback window in minutes. Omit when using absolute timestamps."
            },
            "severity": {
                "type": "string",
                "description": "Optional severity filter such as ERROR, WARN or INFO."
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "description": "Maximum number of logs to return."
            },
            "start_time": {
                "type": "string",
                "description": (
                    "ISO-8601 timestamp with timezone. "
                    "Beginning of an absolute time window."
                )
            },
            "end_time": {
                "type": "string",
                "description": (
                    "ISO-8601 timestamp with timezone. "
                    "End of an absolute time window."
                )
            }
        },
        "required": ["service_name"]
    }
)

RCA_TOOLS = [
    SEARCH_SERVICE_LOGS
]