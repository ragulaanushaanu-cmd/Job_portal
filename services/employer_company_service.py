import models
from sqlalchemy.orm import Session


def get_employer_companies(
    db: Session,
    current_user: models.User,
):
    return (
        db.query(models.Company)
        .filter(
            models.Company.owner_id == current_user.id
        )
        .order_by(models.Company.id.asc())
        .all()
    )