from sqlalchemy.orm import Session

import models


def get_employer_jobs(
    db: Session,
    current_user: models.User,
):
    return (
        db.query(models.Job)
        .join(
            models.Company,
            models.Job.company_id == models.Company.id,
        )
        .filter(
            models.Company.owner_id == current_user.id
        )
        .order_by(models.Job.posted_at.desc())
        .all()
    )