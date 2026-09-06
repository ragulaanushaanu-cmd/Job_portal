from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

import models
from auth import get_current_user
from dependencies import get_db
from schemas import SavedJobListResponse, SavedJobResponse
from services import saved_job_service


router = APIRouter(
    prefix="/saved-jobs",
    tags=["Saved Jobs"]
)


@router.post(
    "/{job_id}",
    response_model=SavedJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a job",
    description="Saves a job to the authenticated user's saved jobs.",
    responses={
        404: {"description": "Job not found"},
        409: {"description": "Job is already saved"},
    },
)
def save_job(
    job_id: int = Path(..., ge=1),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return saved_job_service.save_job(
        db=db,
        user_id=current_user.id,
        job_id=job_id
    )


@router.get(
    "/",
    response_model=SavedJobListResponse,
    summary="Get saved jobs",
    description="Returns the authenticated user's saved jobs with pagination.",
)
def get_my_saved_jobs(
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

    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return saved_job_service.get_my_saved_jobs(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        order=order
    )


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a saved job",
    description="Removes a job from the authenticated user's saved jobs.",
    responses={
        404: {"description": "Saved job not found"},
    },
)
def delete_saved_job(
    job_id: int = Path(..., ge=1),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    saved_job_service.delete_saved_job(
        db=db,
        user_id=current_user.id,
        job_id=job_id
    )

    return None