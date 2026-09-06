import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# ============================================================
# ENVIRONMENT CONFIG
# ============================================================

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured")

# Railway's MySQL_URL uses the generic mysql:// scheme.
# Convert it to the PyMySQL dialect used by this project.
if DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = (
        "mysql+pymysql://"
        + DATABASE_URL[len("mysql://"):]
    )


# ============================================================
# DATABASE ENGINE
# ============================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
)


# ============================================================
# DATABASE SESSION
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# SQLALCHEMY BASE
# ============================================================

Base = declarative_base()