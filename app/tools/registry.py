from app.tools.opensearch_tools import search_service_logs

TOOL_REGISTRY = {
    "search_service_logs": search_service_logs
}

async def execute_tool(
        tool_name: str,
        arguments: dict
):
    """
    Execute only registered tools.
    example: if LLMProvider request below
    {
        "name": "delete_all_logs",
        "arguments": {}
    }

    RootPilot should reject the request as it is not registered.
    """

    if tool_name not in TOOL_REGISTRY:
        raise ValueError(
            f"Tool '{tool_name}' is not registered"
        )

    tool_function = TOOL_REGISTRY[tool_name]

    return await tool_function(**arguments)
