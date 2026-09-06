import logging
import os

from dotenv import load_dotenv
from fastapi import  FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import session

from database import SessionLocal
from exceptions import (
    database_exception_handler,
    general_exception_handler,
    validation_exception_handler,
)

from routers import (
    ats_router,
    employer_company_router,
    employer_dashboard_router,
    employer_jobs_router,
    saved_job_router,
)
from routers.applications import router as applications_router
from routers.auth import router as auth_router
from routers.companies import router as companies_router
from routers.dashboard_router import router as dashboard_router
from routers.jobs import router as jobs_router
from routers.profile_router import router as profile_router
from routers.resumes import router as resumes_router
from routers.users import router as users_router


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# ENVIRONMENT CONFIG
# ============================================================

load_dotenv()

FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

if not FRONTEND_ORIGINS:
    raise RuntimeError(
        "FRONTEND_ORIGINS must contain at least one allowed origin"
    )


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Job Portal API",
    description=(
        "Full-stack job portal API with candidate, employer, "
        "resume, application, and ATS functionality."
    ),
    version="1.0.0",
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# EXCEPTION HANDLERS
# ============================================================

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.add_exception_handler(
    SQLAlchemyError,
    database_exception_handler,
)

app.add_exception_handler(
    Exception,
    general_exception_handler,
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get(
    "/health",
    tags=["Health"],
)
def health_check():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except SQLAlchemyError:
        logger.exception("Health check database failure")

        return {
            "status": "unhealthy",
            "database": "unavailable",
        }


# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    employer_dashboard_router.router
)

app.include_router(
    employer_jobs_router.router
)

app.include_router(
    employer_company_router.router
)

app.include_router(
    resumes_router
)

app.include_router(
    users_router
)

app.include_router(
    companies_router
)

app.include_router(
    jobs_router
)

app.include_router(
    auth_router
)

app.include_router(
    applications_router
)

app.include_router(
    saved_job_router.router
)

app.include_router(
    profile_router
)

app.include_router(
    dashboard_router
)

app.include_router(
    ats_router.router
)