from app.services.history_service import HistoryService


class DummySettings:
    audit_sheet_id = ""
    audit_worksheet_name = "audit_ew"


def test_history_no_sheet_returns_empty(monkeypatch):
    settings = DummySettings()
    service = HistoryService(settings)  # type: ignore[arg-type]

    monkeypatch.setattr(
        service.settings_service,
        "load_runtime_config",
        lambda: {"sheet_id": "", "worksheet_name": "", "google_api_key": ""},
    )
    assert service.get_history(limit=10) == []
