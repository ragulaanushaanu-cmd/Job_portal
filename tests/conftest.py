import pytest
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models
from database import Base
from dependencies import get_db
from main import app


TEST_DATABASE_URL = "sqlite:///./test_job_portal.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# Database session
# ============================================================

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ============================================================
# FastAPI test client
# ============================================================

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ============================================================
# ATS service-level database fixture
# ============================================================

@pytest.fixture
def db_session(db):
    return db


# ============================================================
# ATS candidate user
# ============================================================

@pytest.fixture
def candidate_user(db_session):
    user = models.User(
        username="test_candidate",
        email="test_candidate@example.com",
        password="test_password",
        date_of_birth=date(2000, 1, 1),
        role="Candidate",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


# ============================================================
# ATS resume with completed parsing result
# ============================================================

@pytest.fixture
def resume(db_session, candidate_user):
    resume = models.Resume(
        user_id=candidate_user.id,
        original_filename="test_resume.pdf",
        stored_filename="test_resume_unique.pdf",
        file_type="pdf",
        file_size=1024,
        file_path="uploads/test_resume_unique.pdf",
        is_primary=True,
    )

    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    parsing_result = models.ResumeParsingResult(
        resume_id=resume.id,
        status="Completed",
        extracted_text=(
            "Backend Developer Python FastAPI REST API "
            "SQL PostgreSQL AWS"
        ),
        parsed_data={
            "skills": [
                "Python",
                "FastAPI",
                "REST API",
                "PostgreSQL",
                "AWS",
            ],
            "education": "B.Tech Computer Science",
            "experience": [],
            "projects": [],
        },
        parser_version="2.8",
    )

    db_session.add(parsing_result)
    db_session.commit()
    db_session.refresh(resume)

    return resume


# ============================================================
# ATS employer
# ============================================================

@pytest.fixture
def employer_user(db_session):
    user = models.User(
        username="test_employer",
        email="test_employer@example.com",
        password="test_password",
        date_of_birth=date(1985, 1, 1),
        role="Employer",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


# ============================================================
# ATS company
# ============================================================

@pytest.fixture
def company(db_session, employer_user):
    company = models.Company(
        name="Test ATS Company",
        description="Test company for ATS integration tests",
        location="Hyderabad",
        website="https://example.com",
        owner_id=employer_user.id,
    )

    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)

    return company


# ============================================================
# ATS job
# ============================================================

@pytest.fixture
def job(db_session, company):
    job = models.Job(
        title="Backend Developer",
        description=(
            "We are seeking a Backend Developer with experience "
            "building RESTful API services using Python and FastAPI. "
            "Experience with PostgreSQL and AWS is required."
        ),
        salary=600000,
        location="Hyderabad",
        skills=[
            "Python",
            "FastAPI",
            "REST API",
            "PostgreSQL",
            "AWS",
        ],
        employment_type="Full-time",
        experience_level="Entry",
        work_mode="Remote",
        company_id=company.id,
    )

    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    return job