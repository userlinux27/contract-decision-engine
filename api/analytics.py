from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from utils.logging import log_event

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/event")
async def track_event(request: Request):
    """Receive analytics events from frontend."""
    try:
        data = await request.json()
        event_name = data.get("event", "unknown")
        properties = {k: v for k, v in data.items() if k != "event"}
        
        # Log the event
        log_event(
            properties.get("visitor_id", "anonymous"),
            event_name,
            **properties
        )
        
        return JSONResponse({"status": "ok"})
    except Exception:
        return JSONResponse({"status": "ok"})  # Fail silently


@router.post("/template-source")
async def store_template_source(request: Request):
    """Store template source for attribution (alternative to client-side storage)."""
    try:
        data = await request.json()
        # Could store in Redis/database for cross-device attribution
        # For now, just log
        log_event(
            data.get("visitor_id", "anonymous"),
            "template_source_stored",
            template_slug=data.get("template_slug"),
            page_url=data.get("page_url")
        )
        return JSONResponse({"status": "ok"})
    except Exception:
        return JSONResponse({"status": "ok"})