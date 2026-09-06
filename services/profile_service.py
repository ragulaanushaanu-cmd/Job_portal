from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

import models
from schemas import (
    CandidateProfileCreate,
    CandidateProfileUpdate,
)


def _profile_data_to_db_dict(profile_data):
    data = profile_data.model_dump()

    for field in (
        "linkedin_url",
        "github_url",
        "portfolio_url",
    ):
        if data.get(field) is not None:
            data[field] = str(data[field])

    return data



# ============================================================
# CREATE PROFILE
# ============================================================

def create_profile(
    db: Session,
    user_id: int,
    profile_data: CandidateProfileCreate,
):
    existing_profile = (
        db.query(models.CandidateProfile)
        .filter(
            models.CandidateProfile.user_id == user_id
        )
        .first()
    )

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Candidate profile already exists",
        )

    profile = models.CandidateProfile(
        user_id=user_id,
        **_profile_data_to_db_dict(profile_data),
    )

    try:
        db.add(profile)
        db.commit()
        db.refresh(profile)

        return profile

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Candidate profile already exists",
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create candidate profile",
        )


# ============================================================
# GET PROFILE
# ============================================================

def get_profile(
    db: Session,
    user_id: int,
):
    profile = (
        db.query(models.CandidateProfile)
        .filter(
            models.CandidateProfile.user_id == user_id
        )
        .first()
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found",
        )

    return profile


# ============================================================
# UPDATE PROFILE
# ============================================================

def update_profile(
    db: Session,
    user_id: int,
    profile_data: CandidateProfileUpdate,
):
    profile = (
        db.query(models.CandidateProfile)
        .filter(
            models.CandidateProfile.user_id == user_id
        )
        .first()
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found",
        )

    update_data = profile_data.model_dump(
        exclude_unset=True
    )

    for field in (
        "linkedin_url",
        "github_url",
        "portfolio_url",
    ):
        if update_data.get(field) is not None:
            update_data[field] = str(update_data[field])

    # Only fields defined in CandidateProfileUpdate
    # can reach this point.
    for key, value in update_data.items():
        setattr(profile, key, value)

    try:
        db.commit()
        db.refresh(profile)

        return profile

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile update violates a database constraint",
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update candidate profile",
        )


# ============================================================
# DELETE PROFILE
# ============================================================

def delete_profile(
    db: Session,
    user_id: int,
):
    profile = (
        db.query(models.CandidateProfile)
        .filter(
            models.CandidateProfile.user_id == user_id
        )
        .first()
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate profile not found",
        )

    try:
        db.delete(profile)
        db.commit()

        return {
            "message": "Candidate profile deleted successfully"
        }

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Candidate profile cannot be deleted",
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete candidate profile",
        )