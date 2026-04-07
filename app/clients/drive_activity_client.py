import json
from datetime import datetime, timezone
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


class DriveActivityClient:
    scopes = ["https://www.googleapis.com/auth/drive.activity.readonly"]

    def __init__(self, service_account_info: dict[str, Any]):
        credentials = Credentials.from_service_account_info(
            service_account_info, scopes=self.scopes
        )
        self.client = build("driveactivity", "v2", credentials=credentials, cache_discovery=False)

    def list_activity(self, file_id: str, page_size: int = 50) -> list[dict[str, Any]]:
        request_body = {
            "itemName": f"items/{file_id}",
            "pageSize": page_size,
            "consolidationStrategy": {"none": {}},
        }
        response = self.client.activity().query(body=request_body).execute()
        activities = response.get("activities", [])
        results: list[dict[str, Any]] = []

        for item in activities:
            actor = self._extract_actor(item.get("actors", []))
            action = self._extract_action(item.get("primaryActionDetail", {}))
            timestamp = self._extract_timestamp(item)
            target_title = self._extract_target_title(item.get("targets", []))
            results.append(
                {
                    "source": "drive_activity",
                    "actor": actor,
                    "action": action,
                    "time": timestamp,
                    "ew_id": "",
                    "sheet_name": target_title,
                    "cell_a1": "",
                    "c_key": "",
                    "old_value": "",
                    "new_value": "",
                    "raw": item,
                    "raw_pretty": json.dumps(item, ensure_ascii=False, indent=2),
                }
            )
        return results

    def _extract_actor(self, actors: list[dict[str, Any]]) -> str:
        if not actors:
            return "unknown"
        user_info = actors[0].get("user", {}).get("knownUser", {})
        if "personName" in user_info:
            return user_info["personName"].split("/")[-1]
        if "isCurrentUser" in user_info:
            return "current_user"
        return "unknown"

    def _extract_action(self, detail: dict[str, Any]) -> str:
        if not detail:
            return "unknown"
        return next(iter(detail.keys()), "unknown")

    def _extract_target_title(self, targets: list[dict[str, Any]]) -> str:
        if not targets:
            return ""
        first = targets[0]
        drive_item = first.get("driveItem") or first.get("drive", {})
        title = drive_item.get("title", "")
        if title:
            return str(title)
        name = drive_item.get("name", "")
        if name and "/" in name:
            return name.split("/")[-1]
        return str(name) if name else ""

    def _extract_timestamp(self, activity: dict[str, Any]) -> str:
        if "timestamp" in activity:
            return activity["timestamp"]
        time_range = activity.get("timeRange", {})
        if "endTime" in time_range:
            return time_range["endTime"]
        return datetime.now(timezone.utc).isoformat()
