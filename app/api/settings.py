from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def settings_page(request: Request):
    settings = get_settings()
    service = SettingsService(settings)
    current = service.load_runtime_config()
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={
            "settings": current,
            "gcp_project_id": settings.gcp_project_id,
            "gcp_secret_name": settings.gcp_secret_name,
        },
    )


@router.post("")
async def save_settings(
    sheet_id: str = Form(...),
    worksheet_name: str = Form(...),
    google_api_key: str = Form(""),
    credentials_file: UploadFile = File(...),
):
    settings = get_settings()
    service = SettingsService(settings)
    raw = await credentials_file.read()
    service.upsert_service_account_secret(raw)
    service.save_runtime_config(
        {
            "sheet_id": sheet_id.strip(),
            "worksheet_name": worksheet_name.strip(),
            "google_api_key": google_api_key.strip(),
        }
    )
    return RedirectResponse(url="/settings", status_code=303)


@router.post("/validate")
def validate_current_settings():
    settings = get_settings()
    service = SettingsService(settings)
    config = service.load_runtime_config()
    sheet_id = config.get("sheet_id", "")
    if not sheet_id:
        return JSONResponse({"ok": False, "message": "sheet_id is empty"}, status_code=400)

    ok, message = service.validate_sheet_access(sheet_id)
    status = 200 if ok else 400
    return JSONResponse({"ok": ok, "message": message}, status_code=status)
