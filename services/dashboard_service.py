from sqlalchemy.orm import Session

import models


def get_candidate_dashboard(
    db: Session,
    user_id: int
):
    # -------------------------
    # PROFILE
    # -------------------------

    profile = (
        db.query(models.CandidateProfile)
        .filter(
            models.CandidateProfile.user_id == user_id
        )
        .first()
    )

    # -------------------------
    # RESUMES
    # -------------------------

    resumes = (
        db.query(models.Resume)
        .filter(
            models.Resume.user_id == user_id
        )
        .all()
    )

    total_resumes = len(resumes)

    primary_resume = next(
        (
            resume
            for resume in resumes
            if resume.is_primary
        ),
        None
    )

    primary_resume_id = (
        primary_resume.id
        if primary_resume
        else None
    )

    # -------------------------
    # APPLICATIONS
    # -------------------------

    applications = (
        db.query(models.Application)
        .filter(
            models.Application.user_id == user_id
        )
        .all()
    )

    total_applications = len(applications)

    applied_count = sum(
        1 for application in applications
        if application.status == "Applied"
    )

    shortlisted_count = sum(
        1 for application in applications
        if application.status == "Shortlisted"
    )

    rejected_count = sum(
        1 for application in applications
        if application.status == "Rejected"
    )

    selected_count = sum(
        1 for application in applications
        if application.status == "Selected"
    )
        # -------------------------
    # RECENT APPLICATIONS
    # -------------------------

    recent_applications = sorted(
        applications,
        key=lambda application: application.applied_at,
        reverse=True
    )[:5]

    recent_application_data = [
        {
            "application_id": application.id,
            "job_id": application.job.id,
            "job_title": application.job.title,
            "company_name": application.job.company.name,
            "status": application.status,
            "applied_at": application.applied_at
        }
        for application in recent_applications
    ]

    # -------------------------
    # SAVED JOBS
    # -------------------------

    total_saved_jobs = (
        db.query(models.SavedJob)
        .filter(
            models.SavedJob.user_id == user_id
        )
        .count()
    )

    # -------------------------
    # RETURN DASHBOARD DATA
    # -------------------------

    return {
    "profile": profile,

    "resumes": {
        "total": total_resumes,
        "primary_resume_id": primary_resume_id
    },

    "applications": {
        "total": total_applications,
        "applied": applied_count,
        "shortlisted": shortlisted_count,
        "rejected": rejected_count,
        "selected": selected_count
    },

    "saved_jobs": {
        "total": total_saved_jobs
    },

    "recent_applications": recent_application_data
}