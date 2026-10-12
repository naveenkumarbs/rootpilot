from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "RootPilot"
    app_env: str = "development"

    prometheus_url: str = "http://localhost:9090"
    opensearch_url: str = "http://localhost:9200"

    # LLM provider
    llm_provider: str = "gemini"

    # Agent execution limits
    agent_max_iterations: int = 5
    agent_max_tool_calls: int = 10
    agent_max_execution_seconds: int = 120

    # Gemini 
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"

    # Anthropic
    anthropic_api_key: str | None = None

    # Vertex AI
    vertex_project_id: str | None = None 
    vertex_region: str = "global"
    vertex_claude_model: str = "claude-haiku-4.5@20251001"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()