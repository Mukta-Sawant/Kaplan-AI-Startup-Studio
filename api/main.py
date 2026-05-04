"""
FastAPI application entry point.

Configures CORS, mounts all routers, and provides structured error handling.
"""

from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes.feedback import router as feedback_router
from api.routes.health import router as health_router
from api.routes.phase1 import router as phase1_router
from api.routes.phase2 import router as phase2_router
from api.routes.phase3 import router as phase3_router
from api.routes.phase4 import router as phase4_router
from api.routes.submissions import agent_runs_router, router as submissions_router
from api.routes.upload import router as upload_router
from models.db import IS_SQLITE, Base, engine
from services.env_loader import load_project_env

load_project_env()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(_: FastAPI):
    if IS_SQLITE:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        logger.info("SQLite schema ready for local development.")
    yield

app = FastAPI(
    title="KI Agentic Qualification System",
    description=(
        "Agentic startup qualification platform powered by Anthropic Claude. "
        "Phase 1 runs a parallel EVAL and TEAM agent assessment, producing a "
        "Final Qualification Dossier for human mentor review. "
        "Phase 2 runs a parallel 6-agent Stage One Analysis: INTERACT, DISCOVERY, "
        "COMP, RISK, GTM (parallel), then FIN with GTM context."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

API_PREFIX = "/api"

app.include_router(health_router, prefix=API_PREFIX)
app.include_router(submissions_router, prefix=API_PREFIX)
app.include_router(agent_runs_router, prefix=API_PREFIX)
app.include_router(phase1_router, prefix=API_PREFIX)
app.include_router(phase2_router, prefix=API_PREFIX)
app.include_router(phase3_router, prefix=API_PREFIX)
app.include_router(phase4_router, prefix=API_PREFIX)
app.include_router(feedback_router, prefix=API_PREFIX)
app.include_router(upload_router, prefix=API_PREFIX)

# ---------------------------------------------------------------------------
# Global error handlers
# ---------------------------------------------------------------------------


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    logger.warning("Validation error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "code": "VALIDATION_ERROR"},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled error on %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred.", "code": "INTERNAL_ERROR"},
    )


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "KI Agentic System API", "docs": "/docs"}
