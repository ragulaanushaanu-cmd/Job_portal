from math import ceil

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

import models


def create_application(
    db: Session,
    user_id: int,
    job_id: int,
    resume_id: int | None = None
):
    # ---------------------------------------------------------
    # CHECK JOB
    # ---------------------------------------------------------
    job = (
        db.query(models.Job)
        .filter(models.Job.id == job_id)
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    # ---------------------------------------------------------
    # CHECK DUPLICATE APPLICATION
    # ---------------------------------------------------------
    existing_application = (
        db.query(models.Application)
        .filter(
            models.Application.user_id == user_id,
            models.Application.job_id == job_id
        )
        .first()
    )

    if existing_application:
        raise HTTPException(
            status_code=409,
            detail="You have already applied for this job"
        )

    # ---------------------------------------------------------
    # SELECT RESUME
    # ---------------------------------------------------------
    if resume_id is not None:
        # User explicitly selected a resume.
        # Make sure it belongs to the current user.
        resume = (
            db.query(models.Resume)
            .filter(
                models.Resume.id == resume_id,
                models.Resume.user_id == user_id
            )
            .first()
        )

        if resume is None:
            raise HTTPException(
                status_code=404,
                detail="Resume not found or does not belong to you"
            )

    else:
        # No resume supplied.
        # Automatically use the user's primary resume.
        resume = (
            db.query(models.Resume)
            .filter(
                models.Resume.user_id == user_id,
                models.Resume.is_primary.is_(True)
            )
            .first()
        )

        if resume is None:
            raise HTTPException(
                status_code=400,
                detail="Please upload and set a primary resume before applying"
            )

    # ---------------------------------------------------------
    # CREATE APPLICATION
    # ---------------------------------------------------------
    try:
        new_application = models.Application(
            user_id=user_id,
            job_id=job_id,
            resume_id=resume.id,
            status="Applied"
        )

        db.add(new_application)

        db.flush()

        history = models.ApplicationStatusHistory(
            application_id=new_application.id,
            old_status=None,
            new_status="Applied",
            changed_by=user_id
        )

        db.add(history)

        db.commit()
        db.refresh(new_application)

        return new_application

    except IntegrityError:
        db.rollback()

        # Database-level duplicate protection.
        raise HTTPException(
            status_code=409,
            detail="You have already applied for this job"
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to create application"
        )


def get_my_applications(
    db: Session,
    user_id: int,
    status: str | None = None,
    page: int = 1,
    page_size: int = 10,
    order: str = "desc"
):
    # ---------------------------------------------------------
    # BASE QUERY
    # ---------------------------------------------------------
    query = (
        db.query(models.Application)
        .filter(models.Application.user_id == user_id)
    )

    # ---------------------------------------------------------
    # STATUS FILTER
    # ---------------------------------------------------------
    if status is not None:
        query = query.filter(
            models.Application.status == status
        )

    # ---------------------------------------------------------
    # SORTING
    # ---------------------------------------------------------
    if order == "asc":
        query = query.order_by(
            models.Application.applied_at.asc(),
            models.Application.id.asc()
        )
    else:
        query = query.order_by(
            models.Application.applied_at.desc(),
            models.Application.id.desc()
        )

    # ---------------------------------------------------------
    # PAGINATION
    # ---------------------------------------------------------
    total = query.count()

    total_pages = (
        ceil(total / page_size)
        if total > 0
        else 0
    )

    skip = (page - 1) * page_size

    applications = (
        query
        .offset(skip)
        .limit(page_size)
        .all()
    )

    return {
        "items": applications,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


def get_application(
    db: Session,
    application_id: int,
    current_user: models.User
):
    # ---------------------------------------------------------
    # GET APPLICATION
    # ---------------------------------------------------------
    application = (
        db.query(models.Application)
        .options(
            joinedload(models.Application.user),
            joinedload(
                models.Application.job
            ).joinedload(
                models.Job.company
            ),
            joinedload(models.Application.resume)
        )
        .filter(
            models.Application.id == application_id
        )
        .first()
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    # ---------------------------------------------------------
    # AUTHORIZATION
    #
    # Admin:
    #     Can view any application.
    #
    # Candidate:
    #     Can view their own application.
    #
    # Employer:
    #     Can view applications belonging to jobs posted
    #     by their own company.
    # ---------------------------------------------------------
    is_admin = current_user.role.lower() == "admin"

    is_applicant = (
        application.user_id == current_user.id
    )

    is_job_owner = (
        application.job is not None
        and application.job.company is not None
        and application.job.company.owner_id == current_user.id
    )

    if not (is_admin or is_applicant or is_job_owner):
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this application"
        )

    return application

def get_employer_applications(
    db: Session,
    current_user: models.User,
    status: str | None = None,
    page: int = 1,
    page_size: int = 10,
    order: str = "desc",
):
    # ---------------------------------------------------------
    # BASE QUERY
    # ---------------------------------------------------------

    query = (
        db.query(models.Application)
        .join(
            models.Job,
            models.Application.job_id == models.Job.id
        )
        .join(
            models.Company,
            models.Job.company_id == models.Company.id
        )
        .options(
            joinedload(models.Application.user),
            joinedload(models.Application.job)
            .joinedload(models.Job.company),
            joinedload(models.Application.resume),
        )
    )

    # ---------------------------------------------------------
    # AUTHORIZATION
    # ---------------------------------------------------------

    if current_user.role.lower() == "employer":
        query = query.filter(
            models.Company.owner_id == current_user.id
        )

    elif current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=403,
            detail="Employer or Admin access required"
        )

    # ---------------------------------------------------------
    # STATUS FILTER
    # ---------------------------------------------------------

    if status is not None:
        query = query.filter(
            models.Application.status == status
        )

    # ---------------------------------------------------------
    # SORTING
    # ---------------------------------------------------------

    if order == "asc":
        query = query.order_by(
            models.Application.applied_at.asc(),
            models.Application.id.asc()
        )
    else:
        query = query.order_by(
            models.Application.applied_at.desc(),
            models.Application.id.desc()
        )

    # ---------------------------------------------------------
    # PAGINATION
    # ---------------------------------------------------------

    total = query.count()

    total_pages = (
        ceil(total / page_size)
        if total > 0
        else 0
    )

    skip = (page - 1) * page_size

    applications = (
        query
        .offset(skip)
        .limit(page_size)
        .all()
    )

    return {
        "items": applications,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def update_application(
    db: Session,
    application_id: int,
    status: str,
    current_user: models.User
):
    # ---------------------------------------------------------
    # GET APPLICATION
    # ---------------------------------------------------------
    application = (
        db.query(models.Application)
        .options(
            joinedload(models.Application.user),
            joinedload(
                models.Application.job
            ).joinedload(
                models.Job.company
            ),
            joinedload(models.Application.resume),
        )
        .filter(
            models.Application.id == application_id
        )
        .first()
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    # ---------------------------------------------------------
    # AUTHORIZATION
    #
    # Only Admin or the Employer who owns the company
    # that posted this job can update the application.
    # ---------------------------------------------------------
    is_admin = current_user.role.lower() == "admin"

    is_job_owner = (
        application.job is not None
        and application.job.company is not None
        and application.job.company.owner_id == current_user.id
    )

    if not (is_admin or is_job_owner):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to manage applications for this job"
        )

    # ---------------------------------------------------------
    # STATUS TRANSITIONS
    # ---------------------------------------------------------
    current_status = application.status

    allowed_transitions = {
        "Applied": [
            "Shortlisted",
            "Rejected"
        ],
        "Shortlisted": [
            "Selected",
            "Rejected"
        ],
        "Rejected": [],
        "Selected": []
    }

    # Prevent updating to the same status.
    if status == current_status:
        raise HTTPException(
            status_code=400,
            detail=f"Application is already {current_status}"
        )

    # Validate transition.
    if status not in allowed_transitions.get(
        current_status,
        []
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid status transition: "
                f"{current_status} → {status}"
            )
        )

    # ---------------------------------------------------------
    # UPDATE STATUS
    # ---------------------------------------------------------
    try:
        application.status = status

        history = models.ApplicationStatusHistory(
            application_id=application.id,
            old_status=current_status,
            new_status=status,
            changed_by=current_user.id
        )

        db.add(history)

        db.commit()
        db.refresh(application)

        return application

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to update application status"
        )

def get_application_status_history(
    db: Session,
    application_id: int,
    current_user: models.User
):
    application = (
        db.query(models.Application)
        .options(
            joinedload(
                models.Application.job
            ).joinedload(
                models.Job.company
            )
        )
        .filter(
            models.Application.id == application_id
        )
        .first()
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    # ---------------------------------------------------------
    # AUTHORIZATION
    # ---------------------------------------------------------

    is_admin = (
        current_user.role.lower() == "admin"
    )

    is_applicant = (
        application.user_id == current_user.id
    )

    is_job_owner = (
        application.job is not None
        and application.job.company is not None
        and application.job.company.owner_id == current_user.id
    )

    if not (
        is_admin
        or is_applicant
        or is_job_owner
    ):
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this application history"
        )

    # ---------------------------------------------------------
    # GET HISTORY
    # ---------------------------------------------------------

    return (
        db.query(
            models.ApplicationStatusHistory
        )
        .filter(
            models.ApplicationStatusHistory.application_id
            == application_id
        )
        .order_by(
            models.ApplicationStatusHistory.changed_at.asc(),
            models.ApplicationStatusHistory.id.asc()
        )
        .all()
    )


def delete_application(
    db: Session,
    application_id: int,
    current_user: models.User
):
    # ---------------------------------------------------------
    # GET APPLICATION
    # ---------------------------------------------------------

    application = (
        db.query(models.Application)
        .filter(
            models.Application.id == application_id
        )
        .first()
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    # ---------------------------------------------------------
    # AUTHORIZATION
    #
    # Candidate:
    #     Can delete their own application.
    #
    # Admin:
    #     Can delete any application.
    #
    # Employer:
    #     Cannot delete applications.
    # ---------------------------------------------------------

    is_admin = current_user.role.lower() == "admin"
    is_owner = application.user_id == current_user.id

    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this application"
        )

    # ---------------------------------------------------------
    # DELETE APPLICATION
    # ---------------------------------------------------------

    try:
        db.delete(application)
        db.commit()

        return {
            "message": "Application deleted successfully!"
        }

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to delete application"
        )