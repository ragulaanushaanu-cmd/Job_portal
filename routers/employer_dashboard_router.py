from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas

from auth import get_employer_user
from dependencies import get_db
from services import employer_dashboard_service


router = APIRouter(
    prefix="/employer",
    tags=["Employer Dashboard"]
)


@router.get(
    "/dashboard",
    response_model=schemas.EmployerDashboardResponse,
    summary="Get employer dashboard",
    description=(
        "Returns job, application, company, and related statistics "
        "for the authenticated employer."
    ),
    responses={
        403: {"description": "Employer or administrator access required"},
    },
)
def get_employer_dashboard(
    current_user: models.User = Depends(get_employer_user),
    db: Session = Depends(get_db),
):
    return employer_dashboard_service.get_employer_dashboard(
        db=db,
        current_user=current_user,
    )