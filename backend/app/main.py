"""LearnFlow API — entrypoint FastAPI (async)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db import session as db
from app.schemas.enums import CareerTrack
from app.schemas.meta import CareersResponse, HealthResponse, ReadinessResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await db.dispose_engine()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    # Swagger/ReDoc dimatikan di produksi.
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.app_env == "development" else None,
)

# ── Rate limiting ──────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS (frontend lokal: Vite :5173 / Nginx container :8080) ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,  # tidak ada cookie/session; jangan dibuka tanpa alasan
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization"],
)


# ── Endpoints ──────────────────────────────────────────────────
@app.get("/healthz", response_model=HealthResponse, tags=["ops"])
async def healthz() -> HealthResponse:
    """Liveness: proses hidup. TIDAK menyentuh DB (supaya probe tetap murah)."""
    return HealthResponse(status="ok", service=settings.app_name, version=settings.app_version)


@app.get("/readyz", response_model=ReadinessResponse, tags=["ops"])
async def readyz(response: Response) -> ReadinessResponse:
    """Readiness: koneksi ke PostgreSQL berfungsi (SELECT 1)."""
    if await db.check_db():
        return ReadinessResponse(status="ready", database="up")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status="not_ready", database="down")


@app.get("/api/v1/meta/careers", response_model=CareersResponse, tags=["meta"])
@limiter.limit(settings.rate_limit_default)
async def list_careers(request: Request) -> CareersResponse:  # noqa: ARG001 (dibutuhkan slowapi)
    """Daftar target karier valid (sumber dropdown frontend + Node 0 Sanitizer)."""
    careers = [c.value for c in CareerTrack]
    return CareersResponse(careers=careers, count=len(careers))
