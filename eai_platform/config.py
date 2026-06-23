"""Platform-wide configuration for Cloud Run services."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PlatformSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    gcp_project_id: str = ""
    gcp_region: str = "us-central1"

    # Service URLs (Cloud Run or local docker-compose)
    ai_gateway_url: str = "http://localhost:8080"
    rag_service_url: str = "http://localhost:8081"
    agent_service_url: str = "http://localhost:8082"
    jira_service_url: str = "http://localhost:8083"
    confluence_service_url: str = "http://localhost:8084"
    github_service_url: str = "http://localhost:8085"
    reporting_service_url: str = "http://localhost:8086"

    # Vertex AI
    vertex_location: str = "us-central1"
    gemini_model: str = "gemini-2.0-flash"
    embedding_model: str = "text-embedding-005"
    vector_search_index_id: str = ""
    vector_search_endpoint_id: str = ""
    vector_search_deployed_index_id: str = ""

    # Data layer
    cloud_sql_instance: str = ""
    cloud_sql_database: str = "enterprise_ai"
    cloud_sql_user: str = "postgres"
    cloud_sql_password: str = ""
    database_url: str = "postgresql://postgres:postgres@localhost:5432/enterprise_ai"
    database_sync_url: str = ""
    bigquery_dataset: str = "enterprise_analytics"
    gcs_bucket: str = ""
    gcs_rag_prefix: str = "rag-documents"

    # Integrations
    jira_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    confluence_url: str = ""
    confluence_email: str = ""
    confluence_api_token: str = ""
    github_token: str = ""
    github_org: str = ""

    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "enterprise_ai"

    # Kubernetes
    kubeconfig_path: str = ""
    kubernetes_namespace: str = "default"

    # AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # Slack
    slack_bot_token: str = ""
    slack_team_id: str = ""

    # Browser automation
    browser_headless: bool = True
    browser_timeout_ms: int = 30000
    browser_channel: str = "chrome"
    browser_executable_path: str = ""

    # Local dev fallbacks
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection: str = "enterprise_knowledge"
    use_vertex_ai: bool = False

    service_registry: dict[str, str] = Field(default_factory=dict)

    def model_post_init(self, __context: object) -> None:
        if not self.database_sync_url:
            url = self.database_url
            if url.startswith("postgresql+asyncpg://"):
                url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
            self.database_sync_url = url
        if not self.service_registry:
            self.service_registry = {
                "ai-gateway": self.ai_gateway_url,
                "rag-service": self.rag_service_url,
                "agent-service": self.agent_service_url,
                "jira-service": self.jira_service_url,
                "confluence-service": self.confluence_service_url,
                "github-service": self.github_service_url,
                "reporting-service": self.reporting_service_url,
            }


@lru_cache
def get_settings() -> PlatformSettings:
    return PlatformSettings()
