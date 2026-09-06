from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas

from auth import get_employer_user
from dependencies import get_db
from services import employer_company_service


router = APIRouter(
    prefix="/employer",
    tags=["Employer Companies"],
)


@router.get(
    "/companies",
    response_model=list[schemas.CompanyResponse],
    summary="Get employer companies",
    description="Returns companies associated with the authenticated employer.",
    responses={
        403: {"description": "Employer or administrator access required"},
    },
)
def get_employer_companies(
    current_user: models.User = Depends(get_employer_user),
    db: Session = Depends(get_db),
):
    return employer_company_service.get_employer_companies(
        db=db,
        current_user=current_user,
    )