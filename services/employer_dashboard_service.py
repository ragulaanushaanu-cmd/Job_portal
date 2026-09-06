from sqlalchemy.orm import Session
from sqlalchemy import func

import models


def get_employer_dashboard(
    db: Session,
    current_user: models.User,
):
    # -------------------------------------------------
    # 1. Get companies owned by the current employer
    # -------------------------------------------------

    companies = (
        db.query(models.Company)
        .filter(
            models.Company.owner_id == current_user.id
        )
        .order_by(models.Company.id.asc())
        .all()
    )

    company_ids = [company.id for company in companies]

    # -------------------------------------------------
    # 2. Get total jobs belonging to those companies
    # -------------------------------------------------

    if company_ids:
        total_jobs = (
            db.query(func.count(models.Job.id))
            .filter(
                models.Job.company_id.in_(company_ids)
            )
            .scalar()
        ) or 0
    else:
        total_jobs = 0

    # -------------------------------------------------
    # 3. Application counts
    # -------------------------------------------------

    if company_ids:
        application_counts = (
            db.query(
                func.count(models.Application.id),
                models.Application.status,
            )
            .join(
                models.Job,
                models.Application.job_id == models.Job.id,
            )
            .filter(
                models.Job.company_id.in_(company_ids)
            )
            .group_by(models.Application.status)
            .all()
        )
    else:
        application_counts = []

    status_counts = {
        "Applied": 0,
        "Shortlisted": 0,
        "Rejected": 0,
        "Selected": 0,
    }

    for count, status in application_counts:
        if status in status_counts:
            status_counts[status] = count

    total_applications = sum(status_counts.values())

    # -------------------------------------------------
    # 4. Recent applications
    # -------------------------------------------------

    if company_ids:
        recent_applications = (
            db.query(models.Application)
            .join(
                models.Job,
                models.Application.job_id == models.Job.id,
            )
            .join(
                models.User,
                models.Application.user_id == models.User.id,
            )
            .filter(
                models.Job.company_id.in_(company_ids)
            )
            .order_by(
                models.Application.applied_at.desc()
            )
            .limit(5)
            .all()
        )
    else:
        recent_applications = []

    # -------------------------------------------------
    # 5. Build dashboard response
    # -------------------------------------------------

    return {
        "companies": companies,
        "total_jobs": total_jobs,
        "applications": {
            "total": total_applications,
            "applied": status_counts["Applied"],
            "shortlisted": status_counts["Shortlisted"],
            "rejected": status_counts["Rejected"],
            "selected": status_counts["Selected"],
        },
        "recent_applications": [
            {
                "application_id": application.id,
                "job_id": application.job.id,
                "job_title": application.job.title,
                "candidate_name": application.user.username,
                "status": application.status,
                "applied_at": application.applied_at,
            }
            for application in recent_applications
        ],
    }