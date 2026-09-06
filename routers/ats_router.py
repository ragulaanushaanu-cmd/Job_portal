from fastapi import APIRouter, Depends, Path

from sqlalchemy.orm import Session

from auth import get_candidate_user
from dependencies import get_db

from schemas import ATSAnalysisResponse

import models
from services import ats_service


router = APIRouter(
    prefix="/ats",
    tags=["ATS Analysis"]
)


ATS_ANALYSIS_EXAMPLE = {
    "id": 12,
    "resume_id": 9,
    "job_id": 21,
    "overall_score": "77.50",
    "skill_score": "75.00",
    "experience_score": "100.00",
    "education_score": "100.00",
    "keyword_score": "50.00",
    "matched_skills": [
        "api",
        "fastapi",
        "mysql",
        "python",
        "rest api",
        "sql"
    ],
    "missing_skills": [
        "aws",
        "docker"
    ],
    "matched_keywords": [
        "backend developer"
    ],
    "missing_keywords": [
        "frontend"
    ],
    "recommendations": [
        "Your resume is a strong match.",
        "Add or strengthen missing job-required skills if you genuinely have them.",
        "Improve ATS keyword alignment with relevant job-description terms."
    ],
    "created_at": "2026-09-05T13:12:04",
    "updated_at": "2026-09-05T14:52:03"
}


@router.post(
    "/analyze/{resume_id}/{job_id}",
    response_model=ATSAnalysisResponse,
    summary="Analyze resume against a job",
    description=(
        "Calculates an ATS score by comparing a candidate's parsed resume "
        "against the selected job."
    ),
    responses={
        200: {
            "description": "ATS analysis generated successfully",
            "content": {
                "application/json": {
                    "example": ATS_ANALYSIS_EXAMPLE
                }
            }
        },
        400: {"description": "Resume is not ready for ATS analysis"},
        403: {"description": "Candidate access required"},
        404: {"description": "Resume or job not found"},
        409: {"description": "ATS analysis conflict"},
    },
)
def analyze_resume_against_job(
    resume_id: int = Path(..., ge=1),
    job_id: int = Path(..., ge=1),
    current_user: models.User = Depends(
        get_candidate_user
    ),
    db: Session = Depends(get_db)
):
    return ats_service.analyze_resume_against_job(
        db=db,
        resume_id=resume_id,
        job_id=job_id,
        current_user=current_user
    )


@router.get(
    "/{analysis_id}",
    response_model=ATSAnalysisResponse,
    summary="Get ATS analysis",
    description="Returns a previously generated ATS analysis.",
    responses={
        200: {
            "description": "ATS analysis retrieved successfully",
            "content": {
                "application/json": {
                    "example": ATS_ANALYSIS_EXAMPLE
                }
            }
        },
        403: {"description": "Candidate access required"},
        404: {"description": "ATS analysis not found"},
    },
)
def get_ats_analysis(
    analysis_id: int = Path(..., ge=1),
    current_user: models.User = Depends(
        get_candidate_user
    ),
    db: Session = Depends(get_db)
):
    return ats_service.get_ats_analysis(
        db=db,
        analysis_id=analysis_id,
        current_user=current_user
    )

@router.get(
    "/resume/{resume_id}/job/{job_id}",
    response_model=ATSAnalysisResponse,
    summary="Get ATS analysis for a resume and job",
    description=(
        "Returns the ATS analysis associated with a specific resume and job."
    ),
    responses={
        200: {
            "description": "ATS analysis retrieved successfully",
            "content": {
                "application/json": {
                    "example": ATS_ANALYSIS_EXAMPLE
                }
            }
        },
        403: {"description": "Candidate access required"},
        404: {"description": "ATS analysis not found"},
    },
)
def get_ats_analysis_for_resume_job(
    resume_id: int = Path(..., ge=1),
    job_id: int = Path(..., ge=1),
    current_user: models.User = Depends(
        get_candidate_user
    ),
    db: Session = Depends(get_db)
):
    return ats_service.get_ats_analysis_for_resume_job(
        db=db,
        resume_id=resume_id,
        job_id=job_id,
        current_user=current_user
    )