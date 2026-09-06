from math import ceil

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

import models


def save_job(
    db: Session,
    user_id: int,
    job_id: int
):
    # -------------------------
    # CHECK JOB
    # -------------------------

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

    # -------------------------
    # CHECK DUPLICATE
    # -------------------------

    existing_saved_job = (
        db.query(models.SavedJob)
        .filter(
            models.SavedJob.user_id == user_id,
            models.SavedJob.job_id == job_id
        )
        .first()
    )

    if existing_saved_job is not None:
        raise HTTPException(
            status_code=409,
            detail="You have already saved this job"
        )

    # -------------------------
    # CREATE SAVED JOB
    # -------------------------

    saved_job = models.SavedJob(
        user_id=user_id,
        job_id=job_id
    )

    try:
        db.add(saved_job)
        db.commit()
        db.refresh(saved_job)

        return saved_job

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="You have already saved this job"
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to save job"
        )


def get_my_saved_jobs(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    order: str = "desc"
):
    query = (
        db.query(models.SavedJob)
        .options(
            joinedload(models.SavedJob.job)
            .joinedload(models.Job.company)
        )
        .filter(
            models.SavedJob.user_id == user_id
        )
    )

    # -------------------------
    # SORTING
    # -------------------------

    if order == "asc":
        query = query.order_by(
            models.SavedJob.saved_at.asc(),
            models.SavedJob.id.asc()
        )
    else:
        query = query.order_by(
            models.SavedJob.saved_at.desc(),
            models.SavedJob.id.desc()
        )

    # -------------------------
    # TOTAL COUNT
    # -------------------------

    total = query.count()

    # -------------------------
    # TOTAL PAGES
    # -------------------------

    total_pages = (
        ceil(total / page_size)
        if total > 0
        else 0
    )

    # -------------------------
    # PAGINATION
    # -------------------------

    skip = (page - 1) * page_size

    saved_jobs = (
        query
        .offset(skip)
        .limit(page_size)
        .all()
    )

    return {
        "items": saved_jobs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


def delete_saved_job(
    db: Session,
    user_id: int,
    job_id: int
):
    saved_job = (
        db.query(models.SavedJob)
        .filter(
            models.SavedJob.user_id == user_id,
            models.SavedJob.job_id == job_id
        )
        .first()
    )

    if saved_job is None:
        raise HTTPException(
            status_code=404,
            detail="Saved job not found"
        )

    try:
        db.delete(saved_job)
        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to remove saved job"
        )