from __future__ import annotations

from fastapi import FastAPI

from app.database import init_db
from app.routers import brands, campaigns, features, leads, templates

app = FastAPI(title="Sales Mailer Portal", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(brands.router, prefix="/brands", tags=["brands"])
app.include_router(features.router, prefix="/features", tags=["features"])
app.include_router(templates.router, prefix="/templates", tags=["templates"])
app.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
app.include_router(leads.router, prefix="/leads", tags=["leads"])


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Sales Mailer Portal is running"}
