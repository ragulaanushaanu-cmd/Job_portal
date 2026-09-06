from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas

from auth import get_employer_user
from dependencies import get_db
from services import employer_job_service


router = APIRouter(
    prefix="/employer",
    tags=["Employer Jobs"],
)


@router.get(
    "/jobs",
    response_model=list[schemas.EmployerJobResponse],
    summary="Get employer jobs",
    description="Returns jobs associated with the authenticated employer.",
    responses={
        403: {"description": "Employer or administrator access required"},
    },
)
def get_employer_jobs(
    current_user: models.User = Depends(get_employer_user),
    db: Session = Depends(get_db),
):
    return employer_job_service.get_employer_jobs(
        db=db,
        current_user=current_user,
    )