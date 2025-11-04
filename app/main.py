from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import init_db
from app.routers import brands, campaigns, features, leads, templates

app = FastAPI(title="Sales Mailer Portal", version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(brands.router, prefix="/brands", tags=["brands"])
app.include_router(features.router, prefix="/features", tags=["features"])
app.include_router(templates.router, prefix="/templates", tags=["templates"])
app.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
app.include_router(leads.router, prefix="/leads", tags=["leads"])


@app.get("/", response_class=HTMLResponse)
def root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})
