from typing import Any

import gspread
from google.oauth2.service_account import Credentials


class SheetAuditClient:
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    def __init__(self, service_account_info: dict[str, Any]):
        credentials = Credentials.from_service_account_info(
            service_account_info, scopes=self.scopes
        )
        self.client = gspread.authorize(credentials)

    def list_audit_rows(
        self,
        sheet_id: str,
        worksheet_name: str,
        page_size: int = 50,
    ) -> list[dict[str, str]]:
        worksheet = self.client.open_by_key(sheet_id).worksheet(worksheet_name)
        records = worksheet.get_all_records()
        results: list[dict[str, str]] = []

        for row in records[:page_size]:
            results.append(
                {
                    "source": "sheet_audit",
                    "actor": str(row.get("actor", "unknown")),
                    "action": str(row.get("action", "edit")),
                    "time": str(row.get("time", "")),
                }
            )
        return results
