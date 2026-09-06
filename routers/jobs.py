from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from dependencies import get_db
from auth import get_employer_user
from schemas import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobPaginationResponse,
    JobApplicationListResponse,
    JobDetailResponse,
    EmploymentType,
    ExperienceLevel,
    WorkMode
)
import models
from services import job_service


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)


@router.get(
    "/",
    response_model=JobPaginationResponse,
    summary="Search and list jobs",
    description=(
        "Returns a paginated list of jobs with support for keyword search, "
        "title, location, skill, company, salary, employment type, "
        "experience level, work mode, sorting, and ordering."
    ),
    responses={
        400: {"description": "Invalid salary range"},
    },
)
def get_jobs(
    search: str | None = Query(default=None, min_length=1, max_length=100),
    title: str | None = Query(default=None),
    location: str | None = Query(default=None, min_length=1, max_length=100),
    skill: str | None = Query(default=None, min_length=1, max_length=50),
    company_id: int | None = Query(default=None, ge=1),
    min_salary: Decimal | None = Query(default=None, gt=0),
    max_salary: Decimal | None = Query(default=None, gt=0),
    employment_type: EmploymentType | None = Query(default=None),
    experience_level: ExperienceLevel | None = Query(default=None),
    work_mode: WorkMode | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    sort_by: str = Query(default="id", pattern="^(id|title|salary)$"),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    if min_salary is not None and max_salary is not None and min_salary > max_salary:
        raise HTTPException(
            status_code=400,
            detail="min_salary cannot be greater than max_salary"
        )

    return job_service.get_jobs(
        db=db,
        search=search,
        title=title,
        location=location,
        skill=skill,
        company_id=company_id,
        min_salary=min_salary,
        max_salary=max_salary,
        employment_type=employment_type.value if employment_type else None,
        experience_level=experience_level.value if experience_level else None,
        work_mode=work_mode.value if work_mode else None,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order
    )


@router.get(
    "/{job_id}/applications",
    response_model=JobApplicationListResponse,
    summary="Get applications for a job",
    description="Returns applications submitted to a specific employer job.",
    responses={
        403: {"description": "Employer or administrator access required"},
        404: {"description": "Job not found"},
    },
)
def get_job_applications(
    job_id: int = Path(..., ge=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: models.User = Depends(get_employer_user),
    db: Session = Depends(get_db)
):
    return job_service.get_job_applications(
        db=db,
        job_id=job_id,
        current_user=current_user,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Get job details",
    responses={
        404: {"description": "Job not found"},
    },
)
def get_job(
    job_id: int = Path(..., ge=1),
    db: Session = Depends(get_db)
):
    return job_service.get_job(db=db, job_id=job_id)


@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a job",
    description="Creates a job for a company owned by the authenticated employer.",
    responses={
        403: {"description": "Employer or administrator access required"},
        404: {"description": "Company not found"},
        409: {"description": "Job with the same title already exists for this company"},
    },
)
def create_job(
    job: JobCreate,
    current_user: models.User = Depends(get_employer_user),
    db: Session = Depends(get_db)
):
    return job_service.create_job(
        db=db,
        title=job.title,
        description=job.description,
        salary=job.salary,
        location=job.location,
        skills=job.skills,
        company_id=job.company_id,
        current_user=current_user,
        employment_type=job.employment_type.value,
        experience_level=job.experience_level.value,
        work_mode=job.work_mode.value
    )


@router.put(
    "/{job_id}",
    response_model=JobResponse,
    summary="Update a job",
    responses={
        403: {"description": "Access denied"},
        404: {"description": "Job not found"},
    },
)
def update_job(
    job: JobUpdate,
    job_id: int = Path(..., ge=1),
    current_user: models.User = Depends(get_employer_user),
    db: Session = Depends(get_db)
):
    return job_service.update_job(
        db=db,
        job_id=job_id,
        job_data=job,
        current_user=current_user
    )

@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a job",
    description="Deletes a job according to the authenticated employer's permissions.",
    responses={
        204: {"description": "Job deleted successfully"},
        403: {"description": "Access denied"},
        404: {"description": "Job not found"},
    },
)
def delete_job(
    job_id: int = Path(..., ge=1),
    current_user: models.User = Depends(get_employer_user),
    db: Session = Depends(get_db)
):
    job_service.delete_job(
        db=db,
        job_id=job_id,
        current_user=current_user
    )
    return None