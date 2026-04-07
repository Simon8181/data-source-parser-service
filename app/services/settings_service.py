import json
from pathlib import Path
from typing import Any

from google.cloud import secretmanager

from app.clients.drive_activity_client import DriveActivityClient
from app.config import Settings


class SettingsService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _ensure_parent(self) -> None:
        self.settings.local_config_file.parent.mkdir(parents=True, exist_ok=True)

    def load_runtime_config(self) -> dict[str, Any]:
        if not self.settings.local_config_file.exists():
            return {
                "sheet_id": "",
                "worksheet_name": "",
                "google_api_key": "",
            }
        with self.settings.local_config_file.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    def save_runtime_config(self, config: dict[str, Any]) -> None:
        self._ensure_parent()
        with self.settings.local_config_file.open("w", encoding="utf-8") as fp:
            json.dump(config, fp, ensure_ascii=True, indent=2)

    def upsert_service_account_secret(self, raw_json: bytes) -> str:
        client = secretmanager.SecretManagerServiceClient()
        parent = f"projects/{self.settings.gcp_project_id}"
        secret_name = self.settings.gcp_secret_name
        secret_path = f"{parent}/secrets/{secret_name}"

        try:
            client.get_secret(request={"name": secret_path})
        except Exception:
            client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_name,
                    "secret": {"replication": {"automatic": {}}},
                }
            )

        version = client.add_secret_version(
            request={
                "parent": secret_path,
                "payload": {"data": raw_json},
            }
        )
        return version.name

    def get_service_account_json(self) -> dict[str, Any]:
        client = secretmanager.SecretManagerServiceClient()
        secret_path = (
            f"projects/{self.settings.gcp_project_id}/secrets/"
            f"{self.settings.gcp_secret_name}/versions/latest"
        )
        response = client.access_secret_version(request={"name": secret_path})
        return json.loads(response.payload.data.decode("utf-8"))

    def validate_sheet_access(self, sheet_id: str) -> tuple[bool, str]:
        try:
            sa_info = self.get_service_account_json()
            client = DriveActivityClient(sa_info)
            client.list_activity(file_id=sheet_id, page_size=1)
            return True, "ok"
        except Exception as exc:
            return False, str(exc)
