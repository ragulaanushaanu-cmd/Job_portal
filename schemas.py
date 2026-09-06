from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl

T = TypeVar("T")


class GenericPaginationResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


# =========================
# AUTH & TOKEN
# =========================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


# =========================
# USER
# =========================

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(min_length=8)
    date_of_birth: date


class UserRole(str, Enum):
    CANDIDATE = "Candidate"
    EMPLOYER = "Employer"
    ADMIN = "Admin"


class UserRoleUpdate(BaseModel):
    role: UserRole

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    date_of_birth: date
    role: str


class UserUpdate(BaseModel):
    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=30
    )
    email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)


# =========================
# CANDIDATE PROFILE
# =========================

class CandidateProfileCreate(BaseModel):
    headline: Optional[str] = Field(
        default=None,
        max_length=150
    )

    bio: Optional[str] = Field(
        default=None,
        max_length=1000
    )

    phone: Optional[str] = Field(
        default=None,
        max_length=15
    )

    location: Optional[str] = Field(
        default=None,
        max_length=100
    )

    experience_years: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=3,
        decimal_places=1
    )

    education: Optional[str] = Field(
        default=None,
        max_length=500
    )

    skills: Optional[list[str]] = None

    linkedin_url: Optional[HttpUrl] = Field(
        default=None,
        max_length=255
    )

    github_url: Optional[HttpUrl] = Field(
        default=None,
        max_length=255
    )

    portfolio_url: Optional[HttpUrl] = Field(
        default=None,
        max_length=255
    )


class CandidateProfileUpdate(BaseModel):
    headline: Optional[str] = Field(
        default=None,
        max_length=150
    )

    bio: Optional[str] = Field(
        default=None,
        max_length=1000
    )

    phone: Optional[str] = Field(
        default=None,
        max_length=15
    )

    location: Optional[str] = Field(
        default=None,
        max_length=100
    )

    experience_years: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=3,
        decimal_places=1
    )

    education: Optional[str] = Field(
        default=None,
        max_length=500
    )

    skills: Optional[list[str]] = None

    linkedin_url: Optional[HttpUrl] = Field(
        default=None,
        max_length=255
    )

    github_url: Optional[HttpUrl] = Field(
        default=None,
        max_length=255
    )

    portfolio_url: Optional[HttpUrl] = Field(
        default=None,
        max_length=255
    )


class CandidateProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    headline: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    experience_years: Optional[Decimal] = None
    education: Optional[str] = None
    skills: Optional[list[str]] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# =========================
# COMPANY
# =========================

class CompanyCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=50
    )

    location: str = Field(
        min_length=2,
        max_length=100
    )

    description: Optional[str] = Field(
        default=None,
        max_length=500
    )

    website: Optional[str] = Field(
        default=None,
        max_length=255
    )


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50
    )

    location: Optional[str] = Field(
        default=None,
        max_length=100
    )

    description: Optional[str] = Field(
        default=None,
        max_length=500
    )

    website: Optional[str] = Field(
        default=None,
        max_length=255
    )


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
    description: Optional[str] = None
    website: Optional[str] = None


CompanyPaginationResponse = GenericPaginationResponse[CompanyResponse]


# =========================
# JOB
# =========================

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


class JobCreate(BaseModel):
    title: str = Field(
        min_length=3,
        max_length=100
    )

    description: str = Field(
        min_length=10,
        max_length=2000
    )

    salary: Decimal = Field(
        gt=0,
        decimal_places=2
    )

    location: str = Field(
        min_length=2,
        max_length=100
    )

    skills: list[str] = Field(
        min_length=1
    )

    company_id: int = Field(
        gt=0
    )

    employment_type: EmploymentType = EmploymentType.FULL_TIME

    experience_level: ExperienceLevel = ExperienceLevel.ENTRY

    work_mode: WorkMode = WorkMode.ONSITE

class JobUpdate(BaseModel):
    title: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=100
    )

    description: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=2000
    )

    salary: Optional[Decimal] = Field(
        default=None,
        gt=0,
        decimal_places=2
    )

    location: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    skills: Optional[list[str]] = Field(
        default=None,
        min_length=1
    )

    employment_type: Optional[EmploymentType] = None

    experience_level: Optional[ExperienceLevel] = None

    work_mode: Optional[WorkMode] = None

class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    salary: Decimal
    location: str
    skills: list[str]
    company_id: int

    employment_type: EmploymentType
    experience_level: ExperienceLevel
    work_mode: WorkMode
    posted_at: datetime

# Standardized pagination type alias
JobPaginationResponse = GenericPaginationResponse[JobResponse]


# =========================
# APPLICATION
# =========================

class ApplicationCreate(BaseModel):
    job_id: int = Field(gt=0)
    resume_id: int | None = Field(default=None, gt=0)


class ApplicationStatus(str, Enum):
    Applied = "Applied"
    Shortlisted = "Shortlisted"
    Rejected = "Rejected"
    Selected = "Selected"



class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    job_id: int
    resume_id: Optional[int] = None
    status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[object] = None

# =========================
# APPLICATION DETAILS
# =========================

class ApplicationUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr


class ApplicationCompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str

class JobCompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
    description: Optional[str] = None
    website: Optional[str] = None

class JobDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    salary: Decimal
    location: str
    skills: list[str]
    company_id: int

    employment_type: EmploymentType
    experience_level: ExperienceLevel
    work_mode: WorkMode
    posted_at: datetime

    company: JobCompanyResponse


class ApplicationJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    location: str
    company: ApplicationCompanyResponse


# =========================
# APPLICATION STATUS HISTORY
# =========================

class ApplicationStatusHistoryResponse(BaseModel):
    id: int
    application_id: int
    old_status: str | None
    new_status: str
    changed_by: int | None
    changed_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )

# =========================
# SAVED JOBS
# =========================

class SavedJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    saved_at: datetime


class SavedJobJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    location: str
    salary: Decimal
    skills: list[str]
    company: ApplicationCompanyResponse


class SavedJobDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    saved_at: datetime
    job: SavedJobJobResponse


SavedJobListResponse = GenericPaginationResponse[SavedJobDetailResponse]


# =========================
# RESUME BRIEF
# =========================

class ResumeBriefResponse(BaseModel):
    id: int
    original_filename: str
    file_type: str
    is_primary: bool

    model_config = ConfigDict(from_attributes=True)


class ApplicationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime

    user: ApplicationUserResponse
    job: ApplicationJobResponse
    resume: Optional[ResumeBriefResponse] = None


class JobApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime

    user: ApplicationUserResponse

# =========================
# RESUME
# =========================

class ResumeBase(BaseModel):
    is_primary: bool = False


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    original_filename: str
    file_type: str
    file_size: int
    is_primary: bool
    uploaded_at: datetime
    updated_at: datetime


# =========================
# RESUME PARSING STATUS
# =========================

class ResumeParsingStatus(str, Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    FAILED = "Failed"


# ============================================================
# PARSED RESUME RESPONSE SCHEMAS
# ============================================================

# =========================
# PERSONAL INFORMATION
# =========================

class Personal(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None


# =========================
# PROJECT
# =========================

class Project(BaseModel):
    name: str

    technologies: list[str] = Field(
        default_factory=list
    )

    description: list[str] = Field(
        default_factory=list
    )


# =========================
# EDUCATION
# =========================

class Education(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    university: Optional[str] = None

    cgpa: Optional[float] = None

    start_year: Optional[int] = None
    end_year: Optional[int] = None

    details: list[str] = Field(
        default_factory=list
    )


# =========================
# EXPERIENCE
# =========================

class Experience(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    organization: Optional[str] = None

    start_year: Optional[int] = None
    end_year: Optional[int] = None

    description: list[str] = Field(
        default_factory=list
    )


# =========================
# PARSED RESUME
# =========================

class ParsedResumeResponse(BaseModel):

    personal: Personal = Field(
        default_factory=Personal
    )

    skills: list[str] = Field(
        default_factory=list
    )

    ai_tools: list[str] = Field(
        default_factory=list
    )

    summary: Optional[str] = None

    education: list[Education] = Field(
        default_factory=list
    )

    experience: list[Experience] = Field(
        default_factory=list
    )

    projects: list[Project] = Field(
        default_factory=list
    )

    certifications: list[str] = Field(
        default_factory=list
    )

    languages: list[str] = Field(
        default_factory=list
    )


# ============================================================
# RESUME PARSING RESULT
# ============================================================

class ResumeParsingResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    resume_id: int
    status: ResumeParsingStatus
    extracted_text: Optional[str] = None
    parsed_data: Optional[ParsedResumeResponse] = None
    parser_version: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime



# ============================================================
# ATS ANALYSIS
# ============================================================

class ATSAnalysisResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 12,
                    "resume_id": 9,
                    "job_id": 21,
                    "overall_score": "77.50",
                    "skill_score": "75.00",
                    "experience_score": "100.00",
                    "education_score": "100.00",
                    "keyword_score": "50.00",
                    "matched_skills": [
                        "api",
                        "fastapi",
                        "mysql",
                        "python",
                        "rest api",
                        "sql"
                    ],
                    "missing_skills": [
                        "aws",
                        "docker"
                    ],
                    "matched_keywords": [
                        "backend developer"
                    ],
                    "missing_keywords": [
                        "frontend"
                    ],
                    "recommendations": [
                        "Your resume is a strong match. Focus on the specific areas identified below to improve alignment further.",
                        "Add or strengthen these job-required skills if you genuinely have them.",
                        "Improve ATS keyword alignment by naturally including job-description terms that accurately describe your experience."
                    ],
                    "created_at": "2026-09-05T13:12:04",
                    "updated_at": "2026-09-05T14:52:03"
                }
            ]
        }
    )

    id: int
    resume_id: int
    job_id: int

    overall_score: Decimal = Field(
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2
    )

    skill_score: Decimal = Field(
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2
    )

    experience_score: Decimal = Field(
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2
    )

    education_score: Decimal = Field(
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2
    )

    keyword_score: Decimal = Field(
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2
    )

    matched_skills: list[str] = Field(
        default_factory=list
    )

    missing_skills: list[str] = Field(
        default_factory=list
    )

    matched_keywords: list[str] = Field(
        default_factory=list
    )

    missing_keywords: list[str] = Field(
        default_factory=list
    )

    recommendations: list[str] = Field(
        default_factory=list
    )

    created_at: datetime
    updated_at: datetime


# =========================
# PAGINATION ALIASES
# =========================

ApplicationListResponse = GenericPaginationResponse[ApplicationResponse]

JobApplicationListResponse = GenericPaginationResponse[JobApplicationResponse]

EmployerApplicationListResponse = GenericPaginationResponse[
    ApplicationDetailResponse
]
# =========================
# CANDIDATE DASHBOARD
# =========================

class DashboardProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    headline: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[list[str]] = None


class DashboardResumeResponse(BaseModel):
    total: int
    primary_resume_id: Optional[int] = None


class DashboardApplicationResponse(BaseModel):
    total: int
    applied: int
    shortlisted: int
    rejected: int
    selected: int


class DashboardSavedJobResponse(BaseModel):
    total: int


class DashboardRecentApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    application_id: int
    job_id: int
    job_title: str
    company_name: str
    status: ApplicationStatus
    applied_at: datetime


class CandidateDashboardResponse(BaseModel):
    profile: Optional[DashboardProfileResponse] = None
    resumes: DashboardResumeResponse
    applications: DashboardApplicationResponse
    saved_jobs: DashboardSavedJobResponse
    recent_applications: list[DashboardRecentApplicationResponse]


# =========================
# EMPLOYER DASHBOARD
# =========================

class EmployerDashboardCompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str


class EmployerDashboardJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    location: str
    salary: Decimal
    posted_at: datetime


class EmployerDashboardApplicationResponse(BaseModel):
    total: int
    applied: int
    shortlisted: int
    rejected: int
    selected: int


class EmployerDashboardRecentApplicationResponse(BaseModel):
    application_id: int
    job_id: int
    job_title: str
    candidate_name: str
    status: ApplicationStatus
    applied_at: datetime


class EmployerDashboardResponse(BaseModel):
    companies: list[EmployerDashboardCompanyResponse]
    total_jobs: int
    applications: EmployerDashboardApplicationResponse
    recent_applications: list[EmployerDashboardRecentApplicationResponse]


class EmployerJobResponse(BaseModel):
    id: int
    title: str
    description: str
    salary: Decimal
    location: str
    skills: list[str]
    employment_type: EmploymentType
    experience_level: ExperienceLevel
    work_mode: WorkMode
    posted_at: datetime

    model_config = ConfigDict(from_attributes=True)




