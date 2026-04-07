from typing import Any

from app.clients.drive_activity_client import DriveActivityClient
from app.clients.sheet_audit_client import SheetAuditClient
from app.config import Settings
from app.services.settings_service import SettingsService


class HistoryService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.settings_service = SettingsService(settings)

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        runtime = self.settings_service.load_runtime_config()
        sheet_id = runtime.get("sheet_id", "")
        if not sheet_id:
            return []

        sa_info: dict[str, Any] = self.settings_service.get_service_account_json()
        events: list[dict[str, Any]] = []

        audit_sheet_id = runtime.get("audit_sheet_id", "") or self.settings.audit_sheet_id or ""
        audit_worksheet_name = (
            runtime.get("audit_worksheet_name", "")
            or self.settings.audit_worksheet_name
            or "audit_ew"
        )

        # When audit is configured: only EWid + time from the audit sheet (no Drive Activity).
        if audit_sheet_id and audit_worksheet_name:
            try:
                audit_client = SheetAuditClient(sa_info)
                events.extend(
                    audit_client.list_audit_rows(
                        audit_sheet_id, audit_worksheet_name, page_size=limit
                    )
                )
            except Exception:
                pass
        else:
            try:
                drive_client = DriveActivityClient(sa_info)
                events.extend(drive_client.list_activity(sheet_id, page_size=limit))
            except Exception:
                pass

        events.sort(key=lambda x: x.get("time", ""), reverse=True)
        return events[:limit]
