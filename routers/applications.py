from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

import models
from auth import (
    get_candidate_user,
    get_current_user,
    get_employer_user
)
from dependencies import get_db
from schemas import (
    ApplicationCreate,
    ApplicationDetailResponse,
    ApplicationListResponse,
    EmployerApplicationListResponse,
    ApplicationResponse,
    ApplicationStatus,
    ApplicationUpdate,
    ApplicationStatusHistoryResponse
)
from services import application_service


router = APIRouter(
    prefix="/applications",
    tags=["Applications"]
)


# ============================================================
# CREATE APPLICATION
# Candidate only
# ============================================================

@router.post(
    "/",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a job application",
    description=(
        "Allows a candidate to apply for a job using one of their resumes."
    ),
    responses={
        400: {"description": "Invalid application request"},
        403: {"description": "Candidate access required"},
        404: {"description": "Job or resume not found"},
        409: {"description": "Application already exists"},
    },
)
def create_application(
    application_data: ApplicationCreate,
    current_user: models.User = Depends(get_candidate_user),
    db: Session = Depends(get_db)
):
    return application_service.create_application(
        db=db,
        user_id=current_user.id,
        job_id=application_data.job_id,
        resume_id=application_data.resume_id
    )


# ============================================================
# GET MY APPLICATIONS
# Candidate only
# ============================================================

@router.get(
    "/",
    response_model=ApplicationListResponse,
    summary="Get my applications",
    description=(
        "Returns the authenticated candidate's applications with "
        "optional status filtering, pagination, and ordering."
    ),
    responses={
        403: {"description": "Candidate access required"},
    },
)
def get_my_applications(
    status: ApplicationStatus | None = Query(
        default=None
    ),
    page: int = Query(
        default=1,
        ge=1
    ),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100
    ),
    order: str = Query(
        default="desc",
        pattern="^(asc|desc)$"
    ),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_candidate_user)
):
    return application_service.get_my_applications(
        db=db,
        user_id=current_user.id,
        status=status.value if status else None,
        page=page,
        page_size=page_size,
        order=order
    )

# ============================================================
# GET APPLICATIONS FOR EMPLOYER
#
# Employer:
#     Applications for their company's jobs
#
# Admin:
#     All applications
# ============================================================

@router.get(
    "/employer",
    response_model=EmployerApplicationListResponse,
    summary="Get applications for employer jobs",
    description=(
        "Returns applications for jobs owned by the authenticated employer. "
        "Administrators can access all applications."
    ),
    responses={
        403: {"description": "Employer or administrator access required"},
    },
)
def get_employer_applications(
    status: ApplicationStatus | None = Query(
        default=None
    ),
    page: int = Query(
        default=1,
        ge=1
    ),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100
    ),
    order: str = Query(
        default="desc",
        pattern="^(asc|desc)$"
    ),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_employer_user)
):
    return application_service.get_employer_applications(
        db=db,
        current_user=current_user,
        status=status.value if status else None,
        page=page,
        page_size=page_size,
        order=order
    )

# ============================================================
# GET APPLICATION STATUS HISTORY
#
# Candidate:
#     Own application
#
# Employer:
#     Applications for their company's jobs
#
# Admin:
#     Any application
# ============================================================

@router.get(
    "/{application_id}/history",
    response_model=list[ApplicationStatusHistoryResponse],
    summary="Get application status history",
    description=(
        "Returns the status change history for an application. "
        "Candidates can view their own applications, employers can view "
        "applications for their jobs, and administrators can view any application."
    ),
    responses={
        403: {"description": "Access denied"},
        404: {"description": "Application not found"},
    },
)
def get_application_status_history(
    application_id: int = Path(
        ...,
        ge=1
    ),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return application_service.get_application_status_history(
        db=db,
        application_id=application_id,
        current_user=current_user
    )


# ============================================================
# GET APPLICATION DETAILS
#
# Candidate:
#     Own application
#
# Employer:
#     Applications for their company's jobs
#
# Admin:
#     Any application
# ============================================================

@router.get(
    "/{application_id}",
    response_model=ApplicationDetailResponse,
    summary="Get application details",
    description=(
        "Returns detailed information for an application according to "
        "the authenticated user's role and ownership permissions."
    ),
    responses={
        403: {"description": "Access denied"},
        404: {"description": "Application not found"},
    },
)
def get_application(
    application_id: int = Path(
        ...,
        ge=1
    ),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return application_service.get_application(
        db=db,
        application_id=application_id,
        current_user=current_user
    )


# ============================================================
# UPDATE APPLICATION STATUS
#
# Employer:
#     Own company's job
#
# Admin:
#     Any application
# ============================================================

@router.put(
    "/{application_id}",
    response_model=ApplicationDetailResponse,
    summary="Update application status",
    description=(
        "Updates the status of an application and records the status change "
        "in application status history."
    ),
    responses={
        400: {"description": "Invalid status transition"},
        403: {"description": "Access denied"},
        404: {"description": "Application not found"},
    },
)
def update_application(
    application: ApplicationUpdate,
    application_id: int = Path(
        ...,
        ge=1
    ),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return application_service.update_application(
        db=db,
        application_id=application_id,
        status=application.status.value,
        current_user=current_user
    )


# ============================================================
# DELETE APPLICATION
#
# Candidate:
#     Own application
#
# Admin:
#     Any application
# ============================================================

@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an application",
    description="Deletes an application according to the authenticated user's permissions.",
    responses={
        204: {"description": "Application deleted successfully"},
        403: {"description": "Access denied"},
        404: {"description": "Application not found"},
    },
)
def delete_application(
    application_id: int = Path(
        ...,
        ge=1
    ),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    application_service.delete_application(
        db=db,
        application_id=application_id,
        current_user=current_user
    )

    return None