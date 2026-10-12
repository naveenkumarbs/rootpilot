from app.llm.models import ToolDefinition

SEARCH_SERVICE_LOGS = ToolDefinition(
    name="search_service_logs",
    description=(
        "Search application logs in OpenSearch."
        "Use this tool to investigate service errors, warnings, "
        "timeouts, and dependency failures."
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
                "description": "Lookback window in minutes."
            },
            "severity": {
                "type": "string",
                "description": "Optional severity filter such as ERROR or WARN."
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "description": "Maximum log entries. Prefer 10 to 20."
            }
        },
        "required": ["service_name"]
    }
)

RCA_TOOLS = [
    SEARCH_SERVICE_LOGS
]