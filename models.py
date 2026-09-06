from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


# =========================
# USER
# =========================

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String(50),
        nullable=False
    )

    email = Column(
        String(40),
        unique=True,
        nullable=False,
        index=True
    )

    password = Column(
        String(255),
        nullable=False
    )

    date_of_birth = Column(
        Date,
        nullable=False
    )

    role = Column(
        String(20),
        default="Candidate",  # Can be: "Candidate", "Employer", "Admin"
        nullable=False
    )

    # -------------------------
    # RELATIONSHIPS
    # -------------------------

    applications = relationship(
        "Application",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    resumes = relationship(
        "Resume",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    saved_jobs = relationship(
        "SavedJob",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    candidate_profile = relationship(
        "CandidateProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # NEW: Companies owned by this Employer
    
    companies = relationship(
        "Company",
        back_populates="owner"
    )

# =========================
# CANDIDATE PROFILE
# =========================

class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        unique=True
    )

    headline = Column(
        String(150),
        nullable=True
    )

    bio = Column(
        String(1000),
        nullable=True
    )

    phone = Column(
        String(15),
        nullable=True
    )

    location = Column(
        String(100),
        nullable=True
    )

    experience_years = Column(
        Numeric(3, 1),
        nullable=True
    )

    education = Column(
        String(500),
        nullable=True
    )

    skills = Column(
        JSON,
        nullable=True
    )

    linkedin_url = Column(
        String(255),
        nullable=True
    )

    github_url = Column(
        String(255),
        nullable=True
    )

    portfolio_url = Column(
        String(255),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # -------------------------
    # RELATIONSHIP
    # -------------------------

    user = relationship(
        "User",
        back_populates="candidate_profile"
    )


# =========================
# COMPANY
# =========================

class Company(Base):
    __tablename__ = "companies"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(50),
        unique=True,
        nullable=False
    )

    description = Column(
        String(500),
        nullable=True
    )

    location = Column(
        String(100),
        nullable=False
    )

    website = Column(
        String(255),
        nullable=True
    )

    # NEW: Link Company to User (Employer/Owner)
    owner_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="RESTRICT"
        ),
        nullable=False,
        index=True
    )

    # -------------------------
    # RELATIONSHIPS
    # -------------------------

    owner = relationship(
        "User",
        back_populates="companies"
    )

    jobs = relationship(
        "Job",
        back_populates="company",
        cascade="all, delete-orphan"
    )


class EmploymentType(str, Enum):
    FULL_TIME = "Full-time"
    PART_TIME = "Part-time"
    CONTRACT = "Contract"
    INTERNSHIP = "Internship"


class ExperienceLevel(str, Enum):
    ENTRY = "Entry"
    JUNIOR = "Junior"
    MID = "Mid"
    SENIOR = "Senior"


class WorkMode(str, Enum):
    ONSITE = "Onsite"
    REMOTE = "Remote"
    HYBRID = "Hybrid"


# =========================
# JOB
# =========================

class Job(Base):
    __tablename__ = "jobs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(100),
        nullable=False
    )

    description = Column(
        String(2000),
        nullable=False
    )

    salary = Column(
        Numeric(10, 2),
        nullable=False
    )

    location = Column(
        String(100),
        nullable=False,
        index=True
    )

    skills = Column(
        JSON,
        nullable=False
    )

    employment_type = Column(
        String(20),
        nullable=False,
        default="Full-time",
        index=True
    )

    experience_level = Column(
        String(20),
        nullable=False,
        default="Entry",
        index=True
    )

    work_mode = Column(
        String(20),
        nullable=False,
        default="Onsite",
        index=True
    )

    posted_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    company_id = Column(
        Integer,
        ForeignKey("companies.id"),
        nullable=False,
        index=True
    )

    # -------------------------
    # RELATIONSHIPS
    # -------------------------

    company = relationship(
        "Company",
        back_populates="jobs"
    )

    applications = relationship(
        "Application",
        back_populates="job",
        cascade="all, delete-orphan"
    )

    saved_jobs = relationship(
        "SavedJob",
        back_populates="job",
        cascade="all, delete-orphan"
    )

    ats_analyses = relationship(
        "ATSAnalysis",
        back_populates="job",
        cascade="all, delete-orphan"
    )

    # -------------------------
    # CONSTRAINTS
    # -------------------------

    __table_args__ = (
        UniqueConstraint(
            "title",
            "company_id",
            name="uq_job_title_company"
        ),
    )


# =========================
# SAVED JOB
# =========================

class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    job_id = Column(
        Integer,
        ForeignKey(
            "jobs.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    saved_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # -------------------------
    # RELATIONSHIPS
    # -------------------------

    user = relationship(
        "User",
        back_populates="saved_jobs"
    )

    job = relationship(
        "Job",
        back_populates="saved_jobs"
    )

    # -------------------------
    # CONSTRAINTS
    # -------------------------

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "job_id",
            name="uq_user_saved_job"
        ),
    )


# =========================
# APPLICATION
# =========================

class Application(Base):
    __tablename__ = "applications"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    job_id = Column(
        Integer,
        ForeignKey("jobs.id"),
        nullable=False,
        index=True
    )

    resume_id = Column(
        Integer,
        ForeignKey(
            "resumes.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    status = Column(
        String(20),
        default="Applied",
        nullable=False,
        index=True
    )

    applied_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # -------------------------
    # RELATIONSHIPS
    # -------------------------

    user = relationship(
        "User",
        back_populates="applications"
    )

    job = relationship(
        "Job",
        back_populates="applications"
    )

    resume = relationship(
        "Resume",
        back_populates="applications"
    )

    status_history = relationship(
        "ApplicationStatusHistory",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationStatusHistory.changed_at.asc()"
    )

    # -------------------------
    # CONSTRAINTS
    # -------------------------

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "job_id",
            name="uq_user_job_application"
        ),
    )


# =========================
# APPLICATION STATUS HISTORY
# =========================

class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    application_id = Column(
        Integer,
        ForeignKey(
            "applications.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    old_status = Column(
        String(20),
        nullable=True
    )

    new_status = Column(
        String(20),
        nullable=False,
        index=True
    )

    changed_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    changed_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # -------------------------
    # RELATIONSHIPS
    # -------------------------

    application = relationship(
        "Application",
        back_populates="status_history"
    )

    changed_by_user = relationship(
        "User"
    )


# =========================
# RESUME
# =========================

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    original_filename = Column(
        String(255),
        nullable=False
    )

    stored_filename = Column(
        String(255),
        nullable=False,
        unique=True
    )

    file_type = Column(
        String(20),
        nullable=False
    )

    file_size = Column(
        Integer,
        nullable=False
    )

    file_path = Column(
        String(500),
        nullable=False
    )

    is_primary = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    uploaded_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # -------------------------
    # RELATIONSHIPS
    # -------------------------

    user = relationship(
        "User",
        back_populates="resumes"
    )

    applications = relationship(
        "Application",
        back_populates="resume"
    )

    parsing_result = relationship(
        "ResumeParsingResult",
        back_populates="resume",
        uselist=False,
        cascade="all, delete-orphan"
    )

    ats_analyses = relationship(
        "ATSAnalysis",
        back_populates="resume",
        cascade="all, delete-orphan"
    )

# =========================
# RESUME PARSING RESULT
# =========================

class ResumeParsingResult(Base):
    __tablename__ = "resume_parsing_results"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    resume_id = Column(
        Integer,
        ForeignKey(
            "resumes.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        unique=True,
        index=True
    )

    # -------------------------
    # PARSING STATUS
    # -------------------------

    status = Column(
        String(20),
        nullable=False,
        default="Pending",
        index=True
    )

    # -------------------------
    # EXTRACTED TEXT
    # -------------------------

    extracted_text = Column(
        Text,
        nullable=True
    )

    # -------------------------
    # STRUCTURED PARSED DATA
    # -------------------------

    parsed_data = Column(
        JSON,
        nullable=True
    )

    # -------------------------
    # PARSER INFORMATION
    # -------------------------

    parser_version = Column(
        String(20),
        nullable=True
    )

    error_message = Column(
        String(1000),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # -------------------------
    # RELATIONSHIP
    # -------------------------

    resume = relationship(
        "Resume",
        back_populates="parsing_result"
    )

# ============================================================
# ATS ANALYSIS
# ============================================================

class ATSAnalysis(Base):
    __tablename__ = "ats_analyses"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    resume_id = Column(
        Integer,
        ForeignKey(
            "resumes.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    job_id = Column(
        Integer,
        ForeignKey(
            "jobs.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # -------------------------
    # OVERALL SCORE
    # -------------------------

    overall_score = Column(
        Numeric(5, 2),
        nullable=False
    )

    # -------------------------
    # COMPONENT SCORES
    # -------------------------

    skill_score = Column(
        Numeric(5, 2),
        nullable=False
    )

    experience_score = Column(
        Numeric(5, 2),
        nullable=False
    )

    education_score = Column(
        Numeric(5, 2),
        nullable=False
    )

    keyword_score = Column(
        Numeric(5, 2),
        nullable=False
    )

    # -------------------------
    # MATCHING DETAILS
    # -------------------------

    matched_skills = Column(
        JSON,
        nullable=True
    )

    missing_skills = Column(
        JSON,
        nullable=True
    )

    matched_keywords = Column(
        JSON,
        nullable=True
    )

    missing_keywords = Column(
        JSON,
        nullable=True
    )

    # -------------------------
    # RECOMMENDATIONS
    # -------------------------

    recommendations = Column(
        JSON,
        nullable=True
    )

    # -------------------------
    # TIMESTAMPS
    # -------------------------

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # -------------------------
    # RELATIONSHIPS
    # -------------------------

    resume = relationship(
        "Resume",
        back_populates="ats_analyses"
    )

    job = relationship(
        "Job",
        back_populates="ats_analyses"
    )

    # -------------------------
    # CONSTRAINTS
    # -------------------------

    __table_args__ = (
        UniqueConstraint(
            "resume_id",
            "job_id",
            name="uq_ats_analysis_resume_job",
        ),
    )
