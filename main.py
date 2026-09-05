import json
import os
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.analyze import router as analyze_router
from api.tasks import router as tasks_router
from utils.logging import log_event

app = FastAPI(title="Contract Decision Engine")

# Создаём папки, если их нет
os.makedirs("uploads", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("fixtures", exist_ok=True)

# Отдаём статику (index.html)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем API роутеры
app.include_router(analyze_router)
app.include_router(tasks_router)


@app.get("/static/index.html")
async def redirect_to_home():
    """Редирект на главную страницу."""
    return RedirectResponse(url="/")


@app.get("/", response_class=HTMLResponse)
async def home():
    """Главный экран — единственная страница."""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/analyze/{fixture_type}")
async def analyze_fixture(fixture_type: str):
    """
    Возвращает результат из fixtures/ для демонстрации.
    Без PDF, без LLM — чистый Demo First.

    Поддерживаемые типы: safe, changes, reject
    """
    fixture_map = {
        "safe": "fixtures/safe.json",
        "changes": "fixtures/changes.json",
        "reject": "fixtures/reject.json",
    }

    if fixture_type not in fixture_map:
        return JSONResponse(
            status_code=404,
            content={
                "error": f"Fixture not found. Available: {', '.join(fixture_map.keys())}"
            },
        )

    filepath = fixture_map[fixture_type]

    if not os.path.exists(filepath):
        return JSONResponse(
            status_code=500,
            content={"error": f"Fixture file missing: {filepath}"},
        )

    with open(filepath, "r", encoding="utf-8") as f:
        result = json.load(f)

    log_event("demo", f"fixture_{fixture_type}")

    return JSONResponse(result)


@app.get("/demo/{contract_type}")
async def get_demo(contract_type: str):
    """
    Deprecated: используйте /analyze/{fixture_type}
    Оставлен для обратной совместимости. Перенаправляет на fixtures.
    """
    # Маппим старые названия на новые fixture-типы
    mapping = {
        "service-agreement": "changes",
        "nda": "safe",
        "employment-contract": "reject",
    }

    fixture_type = mapping.get(contract_type)
    if not fixture_type:
        return JSONResponse(
            status_code=404,
            content={"error": "Demo contract not found."},
        )

    return await analyze_fixture(fixture_type)


@app.post("/feedback")
async def feedback(request: Request):
    """Принимает обратную связь после отчёта."""
    data = await request.json()
    visitor_id = data.get("visitor_id", "unknown")
    action = data.get("action", "unknown")
    useful = data.get("useful", None)
    time_to_decision = data.get("time_to_decision", None)

    log_event(
        visitor_id,
        "feedback",
        action=action,
        useful=useful,
        time_to_decision=time_to_decision,
    )

    return JSONResponse({"status": "ok"})


@app.post("/analytics/copy")
async def track_copy(request: Request):
    """Отслеживает копирование suggested wording."""
    data = await request.json()
    visitor_id = data.get("visitor_id", "unknown")
    clause = data.get("clause", "unknown")

    log_event(visitor_id, "copy_wording", clause=clause)

    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
