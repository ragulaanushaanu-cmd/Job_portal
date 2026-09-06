
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

import models
from auth import get_candidate_user
from dependencies import get_db
from schemas import (
    CandidateProfileCreate,
    CandidateProfileUpdate,
    CandidateProfileResponse,
    MessageResponse,
)
from services import profile_service


router = APIRouter(
    prefix="/candidate-profile",
    tags=["Candidate Profile"],
)


# ============================================================
# CREATE CANDIDATE PROFILE
# ============================================================

@router.post(
    "/",
    response_model=CandidateProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create candidate profile",
    description="Creates a profile for the authenticated candidate.",
    responses={
        403: {"description": "Candidate access required"},
        409: {"description": "Candidate profile already exists"},
    },
)
def create_profile(
    profile_data: CandidateProfileCreate,
    current_user: models.User = Depends(get_candidate_user),
    db: Session = Depends(get_db),
):
    return profile_service.create_profile(
        db=db,
        user_id=current_user.id,
        profile_data=profile_data,
    )


# ============================================================
# GET MY PROFILE
# ============================================================
@router.get(
    "/me",
    response_model=CandidateProfileResponse,
    summary="Get my candidate profile",
    description="Returns the authenticated candidate's profile.",
    responses={
        403: {"description": "Candidate access required"},
        404: {"description": "Candidate profile not found"},
    },
)
def get_my_profile(
    current_user: models.User = Depends(get_candidate_user),
    db: Session = Depends(get_db),
):
    return profile_service.get_profile(
        db=db,
        user_id=current_user.id,
    )


# ============================================================
# UPDATE MY PROFILE
# ============================================================

@router.put(
    "/me",
    response_model=CandidateProfileResponse,
    summary="Update my candidate profile",
    description="Updates the authenticated candidate's profile.",
    responses={
        403: {"description": "Candidate access required"},
        404: {"description": "Candidate profile not found"},
    },
)
def update_my_profile(
    profile_data: CandidateProfileUpdate,
    current_user: models.User = Depends(get_candidate_user),
    db: Session = Depends(get_db),
):
    return profile_service.update_profile(
        db=db,
        user_id=current_user.id,
        profile_data=profile_data,
    )


# ============================================================
# DELETE MY PROFILE
# ============================================================

@router.delete(
    "/me",
    response_model=MessageResponse,
    summary="Delete my candidate profile",
    description="Deletes the authenticated candidate's profile.",
    responses={
        403: {"description": "Candidate access required"},
        404: {"description": "Candidate profile not found"},
    },
)
def delete_my_profile(
    current_user: models.User = Depends(get_candidate_user),
    db: Session = Depends(get_db),
):
    return profile_service.delete_profile(
        db=db,
        user_id=current_user.id,
    )


