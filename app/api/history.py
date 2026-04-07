from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.services.history_service import HistoryService

router = APIRouter(tags=["history"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/api/history")
def get_history(limit: int = Query(50, ge=1, le=200)):
    service = HistoryService(get_settings())
    events = service.get_history(limit=limit)
    return JSONResponse({"items": events})


@router.get("/history")
def history_page(request: Request, limit: int = Query(50, ge=1, le=200)):
    service = HistoryService(get_settings())
    events = service.get_history(limit=limit)
    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={"events": events, "limit": limit},
    )
