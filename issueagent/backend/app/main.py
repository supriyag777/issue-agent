import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from .api import analyses, auth, changes, dashboard, guide, issues, repositories
from .core.config import get_settings
from .core.logging import configure_logging, new_request_id, request_id_ctx
from .db.database import create_tables, engine

configure_logging()
settings = get_settings()
log = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version="1.0.0", docs_url="/api/docs", redoc_url="/api/redoc")
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def request_context(request: Request, call_next):
    token = request_id_ctx.set(new_request_id())
    started = time.perf_counter()
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id_ctx.get()
        return response
    finally:
        log.info("request", extra={"operation": f"{request.method} {request.url.path}", "status": "completed", "duration_ms": round((time.perf_counter() - started) * 1000, 2)})
        request_id_ctx.reset(token)


@app.on_event("startup")
def startup() -> None:
    create_tables()


@app.get("/health")
def health() -> dict[str, object]:
    database = "connected"
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        database = "unavailable"
    return {"status": "ok" if database == "connected" else "degraded", "database": database, "github": "configured" if settings.github_configured else "unavailable", "ai": "configured" if settings.ai_configured else "unavailable", "demo_mode": settings.demo_mode}


@app.get("/api/v1/status")
def status() -> dict[str, object]:
    return {"app": settings.app_name, "environment": settings.app_env, "demo_mode": settings.demo_mode, "github_configured": settings.github_configured, "ai_configured": settings.ai_configured}


app.include_router(auth.router)
app.include_router(repositories.router)
app.include_router(issues.router)
app.include_router(analyses.router)
app.include_router(changes.router)
app.include_router(dashboard.router)
app.include_router(guide.router)

frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{path:path}")
    async def frontend(path: str):
        candidate = frontend_dist / path
        if path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(frontend_dist / "index.html")


@app.exception_handler(Exception)
async def unhandled_error(_: Request, exc: Exception):
    log.exception("unhandled_error", extra={"operation": "exception", "status": "error"})
    detail = "Unexpected server error"
    if settings.app_env == "development":
        detail = f"{exc.__class__.__name__}: {exc}"
    return JSONResponse(status_code=500, content={"detail": detail, "type": exc.__class__.__name__})
