import logging

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.history import router as history_router
from app.api.settings import router as settings_router
from app.config import get_settings
from app.middleware.ip_allowlist import IPAllowlistMiddleware

logging.basicConfig(level=logging.INFO)

settings = get_settings()
app = FastAPI(title=settings.app_name)

allowed_entries = [entry.strip() for entry in settings.allowed_ips.split(",") if entry.strip()]
app.add_middleware(IPAllowlistMiddleware, allowed_entries=allowed_entries)

app.include_router(settings_router)
app.include_router(history_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root():
    return RedirectResponse(url="/settings")
