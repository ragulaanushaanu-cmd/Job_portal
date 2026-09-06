from fastapi import APIRouter, Depends, File, Path, UploadFile, status
from sqlalchemy.orm import Session

import models
from auth import get_candidate_user
from dependencies import get_db
from schemas import MessageResponse, ResumeResponse, ResumeParsingResultResponse
from services import resume_service


router = APIRouter(
    prefix="/resumes",
    tags=["Resumes"]
)


# =========================
# UPLOAD RESUME
# =========================

@router.post(
    "/upload",
    response_model=ResumeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a resume",
    description="Uploads a candidate resume for storage and later parsing.",
    responses={
        400: {"description": "Invalid or unsupported resume file"},
        403: {"description": "Candidate access required"},
    },
)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_candidate_user)
):
    return await resume_service.upload_resume(
        db=db,
        user_id=current_user.id,
        file=file
    )


# =========================
# GET MY RESUMES
# =========================

@router.get(
    "/",
    response_model=list[ResumeResponse],
    summary="Get my resumes",
    description="Returns all resumes belonging to the authenticated candidate.",
    responses={
        403: {"description": "Candidate access required"},
    },
)
def get_my_resumes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_candidate_user)
):
    return resume_service.get_user_resumes(
        db=db,
        user_id=current_user.id
    )


# =========================
# DOWNLOAD RESUME
# =========================

@router.get(
    "/{resume_id}/download",
    summary="Download a resume",
    description="Downloads a resume belonging to the authenticated candidate.",
    responses={
        403: {"description": "Candidate access required"},
        404: {"description": "Resume not found"},
    },
)
def download_resume(
    resume_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_candidate_user)
):
    return resume_service.download_resume(
        db=db,
        resume_id=resume_id,
        user_id=current_user.id
    )


# =========================
# SET PRIMARY RESUME
# =========================

@router.put(
    "/{resume_id}/primary",
    response_model=ResumeResponse,
    summary="Set primary resume",
    description="Marks the selected resume as the candidate's primary resume.",
    responses={
        403: {"description": "Candidate access required"},
        404: {"description": "Resume not found"},
    },
)
def set_primary_resume(
    resume_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_candidate_user)
):
    return resume_service.set_primary_resume(
        db=db,
        resume_id=resume_id,
        user_id=current_user.id
    )


# =========================
# DELETE RESUME
# =========================

@router.delete(
    "/{resume_id}",
    response_model=MessageResponse,
    summary="Delete a resume",
    responses={
        403: {"description": "Candidate access required"},
        404: {"description": "Resume not found"},
    },
)
def delete_resume(
    resume_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_candidate_user)
):
    return resume_service.delete_resume(
        db=db,
        resume_id=resume_id,
        user_id=current_user.id
    )

# =========================
# PARSE RESUME
# =========================

@router.post(
    "/{resume_id}/parse",
    response_model=ResumeParsingResultResponse,
    summary="Parse a resume",
    description=(
        "Extracts structured information from the candidate's uploaded resume "
        "and stores the parsing result."
    ),
    responses={
        400: {"description": "Resume cannot be parsed"},
        403: {"description": "Candidate access required"},
        404: {"description": "Resume not found"},
    },
)
def parse_resume(
    resume_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_candidate_user)
):
    return resume_service.parse_resume(
        db=db,
        resume_id=resume_id,
        user_id=current_user.id
    )