import json
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
    ) -> list[dict[str, Any]]:
        worksheet = self.client.open_by_key(sheet_id).worksheet(worksheet_name)
        records = worksheet.get_all_records()
        results: list[dict[str, Any]] = []

        for row in records[:page_size]:
            ew_id = str(
                row.get("ew_id", row.get("EWid", row.get("e_wid", "")))
            )
            time_val = str(row.get("time", ""))
            minimal = {"time": time_val, "ew_id": ew_id}
            results.append(
                {
                    "source": "sheet_audit",
                    "time": time_val,
                    "ew_id": ew_id,
                    "raw": row,
                    "raw_pretty": json.dumps(minimal, ensure_ascii=False, indent=2),
                }
            )
        return results
