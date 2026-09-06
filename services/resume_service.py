import os
import uuid
import zipfile

from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from services import resume_parser_service

import models


# =========================
# CONFIGURATION
# =========================

UPLOAD_DIR = os.getenv(
    "UPLOAD_DIR",
    "uploads"
)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_FILE_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}


# =========================
# FILE VALIDATION
# =========================

def validate_file_signature(
    file_content: bytes,
    file_extension: str
) -> None:
    """
    Validate the actual file content instead of relying
    only on the MIME type supplied by the client.
    """

    # -------------------------
    # PDF
    # -------------------------

    if file_extension == "pdf":

        if not file_content.startswith(b"%PDF"):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file"
            )

        return

    # -------------------------
    # DOCX
    # -------------------------

    if file_extension == "docx":

        if not file_content.startswith(b"PK"):
            raise HTTPException(
                status_code=400,
                detail="Invalid DOCX file"
            )

        try:
            with zipfile.ZipFile(
                __import__("io").BytesIO(file_content)
            ) as zip_file:

                required_files = {
                    "[Content_Types].xml",
                    "word/document.xml",
                }

                file_names = set(zip_file.namelist())

                if not required_files.issubset(file_names):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid DOCX file"
                    )

                # Protect against ZIP bombs / suspicious archives.
                MAX_ZIP_MEMBERS = 1000
                MAX_UNCOMPRESSED_SIZE = 20 * 1024 * 1024  # 20 MB

                members = zip_file.infolist()

                if len(members) > MAX_ZIP_MEMBERS:
                    raise HTTPException(
                        status_code=400,
                        detail="DOCX archive contains too many files"
                    )

                total_uncompressed_size = sum(
                    member.file_size
                    for member in members
                )

                if total_uncompressed_size > MAX_UNCOMPRESSED_SIZE:
                    raise HTTPException(
                        status_code=400,
                        detail="DOCX archive is too large"
                    )

                for member in members:

                    if member.compress_size == 0:
                        if member.file_size > 0:
                            raise HTTPException(
                                status_code=400,
                                detail="Invalid DOCX archive"
                            )
                        continue

                    compression_ratio = (
                        member.file_size / member.compress_size
                    )

                    if compression_ratio > 100:
                        raise HTTPException(
                            status_code=400,
                            detail="Suspicious DOCX archive"
                        )

        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=400,
                detail="Invalid DOCX file"
            )

        return

    raise HTTPException(
        status_code=400,
        detail="Unsupported file type"
    )


# =========================
# GET USER RESUMES
# =========================

def get_user_resumes(
    db: Session,
    user_id: int
):
    return (
        db.query(models.Resume)
        .filter(
            models.Resume.user_id == user_id
        )
        .order_by(
            models.Resume.uploaded_at.desc(),
            models.Resume.id.desc()
        )
        .all()
    )


# =========================
# UPLOAD RESUME
# =========================

async def upload_resume(
    db: Session,
    user_id: int,
    file: UploadFile
):
    # -------------------------
    # 1. VALIDATE MIME TYPE
    # -------------------------

    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed"
        )

    file_extension = ALLOWED_FILE_TYPES[file.content_type]

    # -------------------------
    # 2. VALIDATE ORIGINAL NAME
    # -------------------------

    original_filename = os.path.basename(
        file.filename or ""
    ).strip()

    if not original_filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )

    # Prevent excessively long metadata
    if len(original_filename) > 255:
        raise HTTPException(
            status_code=400,
            detail="Filename is too long"
        )

    # -------------------------
    # 3. READ FILE
    # -------------------------

    file_content = await file.read()

    if not file_content:
        raise HTTPException(
            status_code=400,
            detail="File cannot be empty"
        )

    # -------------------------
    # 4. VALIDATE FILE SIZE
    # -------------------------

    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File size must not exceed 5 MB"
        )

    # -------------------------
    # 5. VALIDATE FILE SIGNATURE
    # -------------------------

    validate_file_signature(
        file_content=file_content,
        file_extension=file_extension
    )

    # -------------------------
    # 6. GENERATE SAFE STORAGE NAME
    # -------------------------

    stored_filename = (
        f"{uuid.uuid4().hex}.{file_extension}"
    )

    os.makedirs(
        UPLOAD_DIR,
        exist_ok=True
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        stored_filename
    )

    # -------------------------
    # 7. SAVE PHYSICAL FILE
    # -------------------------

    try:
        with open(
            file_path,
            "wb"
        ) as buffer:
            buffer.write(file_content)

    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Failed to save resume file"
        )

    # -------------------------
    # 8. DETERMINE PRIMARY STATUS
    # -------------------------

    existing_resume = (
        db.query(models.Resume)
        .filter(
            models.Resume.user_id == user_id
        )
        .first()
    )

    # First resume automatically becomes primary
    is_primary = existing_resume is None

    # -------------------------
    # 9. CREATE DATABASE RECORD
    # -------------------------

    resume = models.Resume(
        user_id=user_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_type=file_extension,
        file_size=len(file_content),
        file_path=file_path,
        is_primary=is_primary
    )

    try:
        db.add(resume)

        db.commit()

        db.refresh(resume)

        return resume

    except SQLAlchemyError:
        db.rollback()

        # Database failed after physical file creation.
        # Remove the orphan file.
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

        raise HTTPException(
            status_code=500,
            detail="Failed to save resume information"
        )


# =========================
# DOWNLOAD RESUME
# =========================

def download_resume(
    db: Session,
    resume_id: int,
    user_id: int
):
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
            detail="Resume not found"
        )

    if not os.path.isfile(resume.file_path):
        raise HTTPException(
            status_code=404,
            detail="Resume file not found on server"
        )

    media_type = {
        "pdf": "application/pdf",
        "docx": (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
    }.get(
        resume.file_type,
        "application/octet-stream"
    )

    return FileResponse(
        path=resume.file_path,
        filename=resume.original_filename,
        media_type=media_type
    )


# =========================
# SET PRIMARY RESUME
# =========================

def set_primary_resume(
    db: Session,
    resume_id: int,
    user_id: int
):
    try:
        # Lock the user's resumes during this transaction.
        resumes = (
            db.query(models.Resume)
            .filter(
                models.Resume.user_id == user_id
            )
            .with_for_update()
            .all()
        )

        resume = next(
            (
                user_resume
                for user_resume in resumes
                if user_resume.id == resume_id
            ),
            None
        )

        if resume is None:
            raise HTTPException(
                status_code=404,
                detail="Resume not found"
            )

        # Remove primary status from all resumes.
        for user_resume in resumes:
            user_resume.is_primary = False

        # Set selected resume as primary.
        resume.is_primary = True

        db.commit()

        db.refresh(resume)

        return resume

    except HTTPException:
        db.rollback()
        raise

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to set primary resume"
        )


# =========================
# DELETE RESUME
# =========================

def delete_resume(
    db: Session,
    resume_id: int,
    user_id: int
):
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
            detail="Resume not found"
        )

    # -------------------------
    # PREVENT DELETE IF USED
    # -------------------------

    linked_application = (
        db.query(models.Application)
        .filter(
            models.Application.resume_id == resume_id
        )
        .first()
    )

    if linked_application is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Resume cannot be deleted because it is "
                "attached to a job application"
            )
        )

    file_path = resume.file_path
    was_primary = resume.is_primary

    try:
        # -------------------------
        # DELETE DATABASE RECORD
        # -------------------------

        db.delete(resume)

        db.flush()

        # -------------------------
        # PROMOTE NEXT RESUME
        # -------------------------

        if was_primary:

            next_primary = (
                db.query(models.Resume)
                .filter(
                    models.Resume.user_id == user_id
                )
                .order_by(
                    models.Resume.uploaded_at.desc(),
                    models.Resume.id.desc()
                )
                .first()
            )

            if next_primary is not None:
                next_primary.is_primary = True

        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Failed to delete resume"
        )

    # -------------------------
    # DELETE PHYSICAL FILE
    # -------------------------

    if os.path.isfile(file_path):

        try:
            os.remove(file_path)

        except OSError:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Resume record deleted, but failed "
                    "to delete resume file"
                )
            )

    return {
        "message": "Resume deleted successfully"
    }


# =========================
# PARSE RESUME
# =========================

def parse_resume(
    db: Session,
    resume_id: int,
    user_id: int
):
    return resume_parser_service.parse_resume(
        db=db,
        resume_id=resume_id,
        user_id=user_id
    )