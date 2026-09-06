from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models

from dependencies import get_db
from auth import get_candidate_user

from schemas import CandidateDashboardResponse

from services import dashboard_service


router = APIRouter(
    prefix="/candidate",
    tags=["Candidate Dashboard"]
)


@router.get(
    "/dashboard",
    response_model=CandidateDashboardResponse,
    summary="Get candidate dashboard",
    description=(
        "Returns application, saved-job, resume, and related statistics "
        "for the authenticated candidate."
    ),
    responses={
        403: {"description": "Candidate access required"},
    },
)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_candidate_user)
):

    return dashboard_service.get_candidate_dashboard(
        db=db,
        user_id=current_user.id
    )