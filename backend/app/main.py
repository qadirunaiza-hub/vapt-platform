from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.db.session import async_engine
from app.db.base import Base
import app.models  # noqa: F401 — ensure all models are registered
from app.api import auth, targets, scans, findings, dashboard
from app.api.reports import router as reports_router, router_download as reports_download_router
from app.api.retests import router as retests_router, retest_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="VAPT Management Platform",
    description="Authorized vulnerability assessment and penetration testing orchestration platform.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(targets.router, prefix="/api/v1")
app.include_router(scans.router, prefix="/api/v1")
app.include_router(findings.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(reports_download_router, prefix="/api/v1")
app.include_router(retests_router, prefix="/api/v1")
app.include_router(retest_router, prefix="/api/v1")


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "vapt-platform"}
