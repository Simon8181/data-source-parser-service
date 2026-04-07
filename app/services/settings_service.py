import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import gspread
from google.cloud import secretmanager
from google.oauth2.service_account import Credentials

from app.clients.drive_activity_client import DriveActivityClient
from app.config import Settings


class SettingsService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _ensure_parent(self) -> None:
        self.settings.local_config_file.parent.mkdir(parents=True, exist_ok=True)
        self.settings.local_service_account_file.parent.mkdir(parents=True, exist_ok=True)

    def load_runtime_config(self) -> dict[str, Any]:
        if not self.settings.local_config_file.exists():
            return {
                "sheet_id": "",
                "worksheet_name": "",
                "google_api_key": "",
                "audit_sheet_id": "",
                "audit_worksheet_name": "audit_ew",
                "credentials_uploaded": False,
                "credentials_updated_at": "",
            }
        with self.settings.local_config_file.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    def save_runtime_config(self, config: dict[str, Any]) -> None:
        self._ensure_parent()
        with self.settings.local_config_file.open("w", encoding="utf-8") as fp:
            json.dump(config, fp, ensure_ascii=True, indent=2)

    def has_uploaded_credentials(self) -> bool:
        if self.settings.local_service_account_file.exists():
            return True
        try:
            _ = self.get_service_account_json()
            return True
        except Exception:
            return False

    def get_credential_status(self) -> dict[str, str]:
        runtime = self.load_runtime_config()
        uploaded = runtime.get("credentials_uploaded", False) or self.has_uploaded_credentials()
        updated_at = runtime.get("credentials_updated_at", "")
        return {
            "uploaded": "yes" if uploaded else "no",
            "updated_at": updated_at,
        }

    def mark_credentials_uploaded(self) -> dict[str, Any]:
        runtime = self.load_runtime_config()
        runtime["credentials_uploaded"] = True
        runtime["credentials_updated_at"] = datetime.now(timezone.utc).isoformat()
        self.save_runtime_config(runtime)
        return runtime

    def validate_service_account_json(self, raw_json: bytes) -> tuple[bool, str]:
        try:
            payload = json.loads(raw_json.decode("utf-8"))
        except Exception:
            return False, "credentials_file is not valid JSON"

        required = {"type", "project_id", "private_key", "client_email", "token_uri"}
        missing = [key for key in required if key not in payload]
        if missing:
            return (
                False,
                "invalid service account json, missing: " + ", ".join(sorted(missing)),
            )
        if payload.get("type") != "service_account":
            return False, "invalid credentials type, expected service_account"
        return True, "ok"

    def upsert_service_account_secret(self, raw_json: bytes) -> str:
        self._ensure_parent()
        try:
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
        except Exception:
            # Local fallback to unblock development without ADC.
            self.settings.local_service_account_file.write_bytes(raw_json)
            return f"local:{self.settings.local_service_account_file}"

    def get_service_account_json(self) -> dict[str, Any]:
        try:
            client = secretmanager.SecretManagerServiceClient()
            secret_path = (
                f"projects/{self.settings.gcp_project_id}/secrets/"
                f"{self.settings.gcp_secret_name}/versions/latest"
            )
            response = client.access_secret_version(request={"name": secret_path})
            return json.loads(response.payload.data.decode("utf-8"))
        except Exception:
            if self.settings.local_service_account_file.exists():
                return json.loads(self.settings.local_service_account_file.read_text(encoding="utf-8"))
            raise

    def _friendly_sheet_error(self, message: str) -> str:
        if "<Response [404]>" in message or "404" in message:
            return (
                "sheet not found or no permission. "
                "Please check sheet_id and share the sheet with the service account email."
            )
        if "PERMISSION_DENIED" in message or "403" in message:
            return "permission denied. Please share the sheet with the service account email."
        return f"sheet check failed: {message}"

    def _friendly_drive_error(self, message: str) -> str:
        if "Internal error encountered" in message:
            return "drive activity api temporarily unavailable (500)"
        if "404" in message:
            return "drive activity api cannot find this file; verify sheet_id and Drive access."
        if "403" in message:
            return "drive activity api permission denied; enable API and grant access."
        return f"drive activity warning: {message}"

    def validate_sheet_access(self, sheet_id: str) -> tuple[bool, str]:
        try:
            sa_info = self.get_service_account_json()
            # Primary validation: verify the sheet is readable.
            sheets_creds = Credentials.from_service_account_info(
                sa_info, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
            )
            sheets_client = gspread.authorize(sheets_creds)
            spreadsheet = sheets_client.open_by_key(sheet_id)
            _ = spreadsheet.title

            # Secondary validation: Drive Activity can be flaky with transient 500.
            try:
                drive_client = DriveActivityClient(sa_info)
                drive_client.list_activity(file_id=sheet_id, page_size=1)
                return True, "ok"
            except Exception as drive_exc:
                drive_message = str(drive_exc)
                return True, f"sheet read ok; {self._friendly_drive_error(drive_message)}"
        except Exception as exc:
            message = str(exc)
            if "missing fields client_email, token_uri" in message:
                return (
                    False,
                    "credentials file is not a Service Account key. "
                    "Please upload a JSON key created from IAM > Service Accounts > Keys.",
                )
            return False, self._friendly_sheet_error(message)
