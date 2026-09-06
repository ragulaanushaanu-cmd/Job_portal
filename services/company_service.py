from math import ceil

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

import models


# ============================================================
# CREATE COMPANY
# ============================================================

def create_company(
    db: Session,
    name: str,
    location: str,
    description: str | None,
    website: str | None,
    owner_id: int,
):
    # --------------------------------------------------------
    # Normalize input
    # --------------------------------------------------------

    name = name.strip()
    location = location.strip()

    description = (
        description.strip()
        if description
        else None
    )

    website = (
        website.strip()
        if website
        else None
    )

    # --------------------------------------------------------
    # Basic service-level validation
    # --------------------------------------------------------

    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Company name cannot be empty",
        )

    if not location:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Company location cannot be empty",
        )

    # --------------------------------------------------------
    # Duplicate company check
    # --------------------------------------------------------

    existing_company = (
        db.query(models.Company)
        .filter(
            models.Company.name.ilike(name)
        )
        .first()
    )

    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company already exists",
        )

    # --------------------------------------------------------
    # Create company
    # --------------------------------------------------------

    new_company = models.Company(
        name=name,
        location=location,
        description=description,
        website=website,
        owner_id=owner_id,
    )

    try:
        db.add(new_company)
        db.commit()
        db.refresh(new_company)

        return new_company

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company already exists or violates a database constraint",
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create company",
        )


# ============================================================
# GET ALL COMPANIES
# ============================================================


def get_companies(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
    location: str | None = None,
    sort_by: str = "id",
    order: str = "asc",
):
    query = db.query(models.Company)

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    if search:
        search = search.strip()

        if search:
            query = query.filter(
                models.Company.name.ilike(
                    f"%{search}%"
                )
            )

    # --------------------------------------------------------
    # Location filter
    # --------------------------------------------------------

    if location:
        location = location.strip()

        if location:
            query = query.filter(
                models.Company.location.ilike(
                    f"%{location}%"
                )
            )

    # --------------------------------------------------------
    # Sorting
    # --------------------------------------------------------

    sort_columns = {
        "id": models.Company.id,
        "name": models.Company.name,
        "location": models.Company.location,
    }

    sort_column = sort_columns.get(
        sort_by,
        models.Company.id,
    )

    if order.lower() == "desc":
        query = query.order_by(
            sort_column.desc()
        )
    else:
        query = query.order_by(
            sort_column.asc()
        )

    # --------------------------------------------------------
    # Pagination
    # --------------------------------------------------------

    total = query.count()

    total_pages = (
        ceil(total / page_size)
        if total > 0
        else 0
    )

    offset = (page - 1) * page_size

    companies = (
        query
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return {
        "items": companies,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }

# ============================================================
# GET SINGLE COMPANY
# ============================================================

def get_company(
    db: Session,
    company_id: int,
):
    company = (
        db.query(models.Company)
        .filter(
            models.Company.id == company_id
        )
        .first()
    )

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return company


# ============================================================
# GET COMPANY JOBS
# ============================================================

def get_company_jobs(
    db: Session,
    company_id: int,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "id",
    order: str = "asc",
):
    # --------------------------------------------------------
    # Make sure company exists
    # --------------------------------------------------------

    get_company(
        db=db,
        company_id=company_id,
    )

    # --------------------------------------------------------
    # Base query
    # --------------------------------------------------------

    query = (
        db.query(models.Job)
        .filter(
            models.Job.company_id == company_id
        )
    )

    # --------------------------------------------------------
    # Sorting
    # --------------------------------------------------------

    sort_columns = {
        "id": models.Job.id,
        "title": models.Job.title,
        "salary": models.Job.salary,
    }

    sort_column = sort_columns.get(
        sort_by,
        models.Job.id,
    )

    if order.lower() == "desc":
        query = query.order_by(
            sort_column.desc()
        )
    else:
        query = query.order_by(
            sort_column.asc()
        )

    # --------------------------------------------------------
    # Pagination
    # --------------------------------------------------------

    total = query.count()

    total_pages = (
        ceil(total / page_size)
        if total > 0
        else 0
    )

    offset = (page - 1) * page_size

    jobs = (
        query
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return {
        "items": jobs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# ============================================================
# UPDATE COMPANY
# ============================================================

def update_company(
    db: Session,
    company_id: int,
    company_data,
    current_user: models.User,
):
    company = get_company(
        db=db,
        company_id=company_id,
    )

    # --------------------------------------------------------
    # Authorization
    # --------------------------------------------------------

    is_admin = (
        current_user.role.lower() == "admin"
    )

    is_owner = (
        company.owner_id == current_user.id
    )

    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this company",
        )

    # --------------------------------------------------------
    # Extract only supplied fields
    # --------------------------------------------------------

    update_data = company_data.model_dump(
        exclude_unset=True
    )

    # --------------------------------------------------------
    # Normalize text fields
    # --------------------------------------------------------

    if "name" in update_data:
        update_data["name"] = (
            update_data["name"].strip()
        )

        if not update_data["name"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Company name cannot be empty",
            )

    if "location" in update_data:
        update_data["location"] = (
            update_data["location"].strip()
        )

        if not update_data["location"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Company location cannot be empty",
            )

    if "description" in update_data:
        if update_data["description"]:
            update_data["description"] = (
                update_data["description"].strip()
            )

            if not update_data["description"]:
                update_data["description"] = None

    if "website" in update_data:
        if update_data["website"]:
            update_data["website"] = (
                update_data["website"].strip()
            )

            if not update_data["website"]:
                update_data["website"] = None

    # --------------------------------------------------------
    # Duplicate company name check
    # --------------------------------------------------------

    if "name" in update_data:
        existing_company = (
            db.query(models.Company)
            .filter(
                models.Company.name.ilike(
                    update_data["name"]
                ),
                models.Company.id != company_id,
            )
            .first()
        )

        if existing_company:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Company name already exists",
            )

    # --------------------------------------------------------
    # Apply changes
    # --------------------------------------------------------

    for key, value in update_data.items():
        setattr(company, key, value)

    try:
        db.commit()
        db.refresh(company)

        return company

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company update violates a database constraint",
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company",
        )


# ============================================================
# DELETE COMPANY
# ============================================================

def delete_company(
    db: Session,
    company_id: int,
    current_user: models.User,
):
    company = get_company(
        db=db,
        company_id=company_id,
    )

    # --------------------------------------------------------
    # Authorization
    # --------------------------------------------------------

    is_admin = (
        current_user.role.lower() == "admin"
    )

    is_owner = (
        company.owner_id == current_user.id
    )

    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this company",
        )

    # --------------------------------------------------------
    # Business protection
    # --------------------------------------------------------
    # A company with jobs cannot be deleted.
    #
    # This is safer than deleting a company and accidentally
    # affecting job records.
    # --------------------------------------------------------

    has_jobs = (
        db.query(models.Job)
        .filter(
            models.Job.company_id == company_id
        )
        .first()
    )

    if has_jobs:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Company cannot be deleted because "
                "jobs are associated with this company"
            ),
        )

    # --------------------------------------------------------
    # Delete
    # --------------------------------------------------------

    try:
        db.delete(company)
        db.commit()

        return {
            "message": "Company deleted successfully"
        }

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Company cannot be deleted because "
                "it is linked to existing records"
            ),
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete company",
        )