from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "sheet-history-service"
    app_env: str = "dev"
    host: str = "0.0.0.0"
    port: int = 8000

    # Comma-separated allowlist, supports plain IP and CIDR.
    allowed_ips: str = "127.0.0.1/32"

    # Config metadata on local disk (non-secret).
    local_config_file: Path = Path("config/runtime_settings.json")

    gcp_project_id: str = ""
    gcp_secret_name: str = "sheet-service-account-json"

    # Optional sheet audit log source.
    audit_sheet_id: str = ""
    audit_worksheet_name: str = "audit_log"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
