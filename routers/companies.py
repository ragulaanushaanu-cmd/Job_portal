from fastapi import (
    APIRouter,
    Depends,
    Path,
    Query,
    status,
)

from sqlalchemy.orm import Session

from auth import get_employer_user
from dependencies import get_db

import models
import schemas

from services import company_service


router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


# ============================================================
# CREATE COMPANY
# ============================================================

@router.post(
    "/",
    response_model=schemas.CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a company",
    description="Creates a company owned by the authenticated employer.",
    responses={
        403: {"description": "Employer or administrator access required"},
        409: {"description": "Company already exists"},
    },
)
def create_company(
    company_in: schemas.CompanyCreate,
    current_user: models.User = Depends(
        get_employer_user
    ),
    db: Session = Depends(get_db),
):
    return company_service.create_company(
        db=db,
        name=company_in.name,
        location=company_in.location,
        description=company_in.description,
        website=company_in.website,
        owner_id=current_user.id,
    )


# ============================================================
# GET ALL COMPANIES
# ============================================================

@router.get(
    "/",
    response_model=schemas.CompanyPaginationResponse,
    summary="List companies",
    description=(
        "Returns a paginated list of companies with optional search, "
        "location filtering, sorting, and ordering."
    ),
)
def get_companies(
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    location: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    sort_by: str = Query(
        default="id",
        pattern="^(id|name|location)$",
    ),
    order: str = Query(
        default="asc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
):
    return company_service.get_companies(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        location=location,
        sort_by=sort_by,
        order=order,
    )


# ============================================================
# GET SINGLE COMPANY
# ============================================================

@router.get(
    "/{company_id}",
    response_model=schemas.CompanyResponse,
    summary="Get a company",
    responses={
        404: {"description": "Company not found"},
    },
)
def get_company(
    company_id: int = Path(
        ...,
        ge=1,
    ),
    db: Session = Depends(get_db),
):
    return company_service.get_company(
        db=db,
        company_id=company_id,
    )


# ============================================================
# GET COMPANY JOBS
# ============================================================

@router.get(
    "/{company_id}/jobs",
    response_model=schemas.JobPaginationResponse,
    summary="Get jobs for a company",
    description="Returns a paginated list of jobs belonging to a company.",
    responses={
        404: {"description": "Company not found"},
    },
)
def get_company_jobs(
    company_id: int = Path(
        ...,
        ge=1,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    sort_by: str = Query(
        default="id",
        pattern="^(id|title|salary)$",
    ),
    order: str = Query(
        default="asc",
        pattern="^(asc|desc)$",
    ),
    db: Session = Depends(get_db),
):
    return company_service.get_company_jobs(
        db=db,
        company_id=company_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order,
    )


# ============================================================
# UPDATE COMPANY
# ============================================================

@router.put(
    "/{company_id}",
    response_model=schemas.CompanyResponse,
    summary="Update a company",
    description="Updates a company according to the authenticated user's ownership permissions.",
    responses={
        403: {"description": "Access denied"},
        404: {"description": "Company not found"},
    },
)
def update_company(
    company_data: schemas.CompanyUpdate,
    company_id: int = Path(
        ...,
        ge=1,
    ),
    current_user: models.User = Depends(
        get_employer_user
    ),
    db: Session = Depends(get_db),
):
    return company_service.update_company(
        db=db,
        company_id=company_id,
        company_data=company_data,
        current_user=current_user,
    )


# ============================================================
# DELETE COMPANY
# ============================================================

@router.delete(
    "/{company_id}",
    response_model=schemas.MessageResponse,
    summary="Delete a company",
    description="Deletes a company according to the authenticated user's permissions.",
    responses={
        403: {"description": "Access denied"},
        404: {"description": "Company not found"},
        409: {"description": "Company cannot be deleted because it is still referenced"},
    },
)
def delete_company(
    company_id: int = Path(
        ...,
        ge=1,
    ),
    current_user: models.User = Depends(
        get_employer_user
    ),
    db: Session = Depends(get_db),
):
    return company_service.delete_company(
        db=db,
        company_id=company_id,
        current_user=current_user,
    )