import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import markdown

from api.analyze import router as analyze_router
from api.tasks import router as tasks_router
from api.analytics import router as analytics_router
from utils.logging import log_event

# Public Base URL from environment (for canonical URLs, sitemap, etc.)
# Defaults to production domain, can be overridden for local dev
BASE_URL = os.getenv("BASE_URL", "https://contract.workmatic.pro").rstrip("/")

app = FastAPI(title="Contract Decision Engine")

# Создаём папки, если их нет
os.makedirs("uploads", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("fixtures", exist_ok=True)

# Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Отдаём статику (index.html)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем API роутеры
app.include_router(analyze_router)
app.include_router(tasks_router)
app.include_router(analytics_router)


def load_template_metadata(slug: str) -> dict | None:
    """Load template metadata from JSON file."""
    json_path = Path(f"content/templates/{slug}.json")
    if not json_path.exists():
        return None
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_template_document(slug: str) -> str:
    """Load template document from Markdown file and convert to HTML."""
    md_path = Path(f"content/templates/{slug}.md")
    if not md_path.exists():
        return "<p>Document not available.</p>"
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    return markdown.markdown(md_content, extensions=["tables", "fenced_code"])


def list_all_templates() -> list[dict]:
    """List all available templates with basic metadata."""
    templates_dir = Path("content/templates")
    result = []
    for json_file in templates_dir.glob("*.json"):
        slug = json_file.stem
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Determine category from slug
        category = "services"
        if "nda" in slug or "non-disclosure" in slug:
            category = "confidentiality"
        elif "msa" in slug or "master-services" in slug:
            category = "ongoing"

        result.append({
            "slug": slug,
            "title": data.get("h1", slug),
            "subtitle": data.get("subtitle", ""),
            "jurisdiction": data.get("jurisdiction", ""),
            "last_updated": data.get("last_updated", ""),
            "category": category,
        })
    return sorted(result, key=lambda x: x["title"])


@app.get("/static/index.html")
async def redirect_to_home():
    """Редирект на главную страницу."""
    return RedirectResponse(url="/")


@app.get("/", response_class=HTMLResponse)
async def home():
    """Главный экран — единственная страница."""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/robots.txt")
async def robots():
    """Robots.txt for search engines."""
    body = f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n"
    return HTMLResponse(content=body, media_type="text/plain")


@app.get("/templates", response_class=HTMLResponse)
async def templates_catalog(request: Request):
    """Templates catalog page."""
    all_templates = list_all_templates()
    return templates.TemplateResponse("templates/catalog.html", {
        "request": request,
        "templates": all_templates,
        "base_url": BASE_URL,
    })


@app.get("/templates/{slug}", response_class=HTMLResponse)
async def template_page(request: Request, slug: str):
    """Individual template page."""
    metadata = load_template_metadata(slug)
    if not metadata:
        return HTMLResponse(content="Template not found", status_code=404)
    
    document_html = load_template_document(slug)
    
    # Get related templates (same jurisdiction, excluding current)
    all_templates = list_all_templates()
    related = [t for t in all_templates if t["slug"] != slug and t["jurisdiction"] == metadata.get("jurisdiction")][:3]
    
    # Build canonical URL
    canonical_url = f"{BASE_URL}/templates/{slug}"
    
    return templates.TemplateResponse("templates/detail.html", {
        "request": request,
        "template": metadata,
        "document_html": document_html,
        "related_templates": related,
        "canonical_url": canonical_url,
    })


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


@app.get("/sitemap.xml", response_class=HTMLResponse)
async def sitemap():
    """Generate sitemap.xml with all template URLs."""
    all_templates = list_all_templates()

    # Base URLs
    urls = [
        f"{BASE_URL}/",
        f"{BASE_URL}/templates",
        f"{BASE_URL}/tools/contract-risk-checker",
    ]

    # Template URLs
    for t in all_templates:
        urls.append(f"{BASE_URL}/templates/{t['slug']}")

    # Generate XML
    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for url in urls:
        xml_parts.append(f'  <url>')
        xml_parts.append(f'    <loc>{url}</loc>')
        xml_parts.append(f'    <changefreq>weekly</changefreq>')
        xml_parts.append(f'    <priority>0.8</priority>')
        xml_parts.append(f'  </url>')

    xml_parts.append('</urlset>')

    return HTMLResponse(content="\n".join(xml_parts), media_type="application/xml")


@app.get("/tools/contract-risk-checker", response_class=HTMLResponse)
async def tool_page(request: Request):
    """Free Contract Risk Checker tool page."""
    return templates.TemplateResponse("templates/tool.html", {
        "request": request,
        "base_url": BASE_URL,
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

