from math import ceil
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

import models


def get_jobs(
    db: Session,
    search: str | None = None,
    location: str | None = None,
    title: str | None = None,
    company_id: int | None = None,
    min_salary: Decimal | None = None,
    max_salary: Decimal | None = None,
    skill: str | None = None,
    employment_type: str | None = None,
    experience_level: str | None = None,
    work_mode: str | None = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "id",
    order: str = "asc"
):
    query = db.query(models.Job)

    # NORMALIZE INPUT
    if search:
        search = search.strip()
    if location:
        location = location.strip()
    if title:
        title = title.strip()
    if skill:
        skill = skill.strip()

    # KEYWORD SEARCH
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            models.Job.title.ilike(search_term)
            | models.Job.description.ilike(search_term)
            | models.Job.location.ilike(search_term)
        )

    # FILTERS
    if location:
        query = query.filter(models.Job.location.ilike(f"%{location}%"))

    if title:
        query = query.filter(models.Job.title.ilike(f"%{title}%"))

    if company_id is not None:
        query = query.filter(models.Job.company_id == company_id)

    if min_salary is not None:
        query = query.filter(models.Job.salary >= min_salary)

    if max_salary is not None:
        query = query.filter(models.Job.salary <= max_salary)

    if employment_type:
        query = query.filter(models.Job.employment_type == employment_type)

    if experience_level:
        query = query.filter(models.Job.experience_level == experience_level)

    if work_mode:
        query = query.filter(models.Job.work_mode == work_mode)

    if skill:
        skill = skill.lower()
        query = query.filter(models.Job.skills.contains([skill]))

    # SORTING
    if sort_by == "salary":
        sort_column = models.Job.salary
    elif sort_by == "title":
        sort_column = models.Job.title
    else:
        sort_column = models.Job.id

    if order == "desc":
        query = query.order_by(sort_column.desc(), models.Job.id.desc())
    else:
        query = query.order_by(sort_column.asc(), models.Job.id.asc())

    # COUNT & PAGINATION
    total = query.count()
    total_pages = ceil(total / page_size) if total else 0
    skip = (page - 1) * page_size

    jobs = query.offset(skip).limit(page_size).all()

    return {
        "items": jobs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


def get_job_applications(
    db: Session,
    job_id: int,
    current_user: models.User,
    page: int = 1,
    page_size: int = 10
):
    job = (
        db.query(models.Job)
        .options(joinedload(models.Job.company))
        .filter(models.Job.id == job_id)
        .first()
    )

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Ownership Guard: Employer can only view applications for their own company's jobs
    if current_user.role.lower() != "admin" and job.company.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view applications for this job"
        )

    query = (
        db.query(models.Application)
        .options(joinedload(models.Application.user))
        .filter(models.Application.job_id == job_id)
    )

    total = query.count()
    skip = (page - 1) * page_size

    applications = (
        query.order_by(models.Application.id.desc())
        .offset(skip)
        .limit(page_size)
        .all()
    )

    total_pages = ceil(total / page_size) if total > 0 else 0

    return {
        "items": applications,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


def get_job(db: Session, job_id: int):
    job = (
        db.query(models.Job)
        .options(joinedload(models.Job.company))
        .filter(models.Job.id == job_id)
        .first()
    )

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


def create_job(
    db: Session,
    title: str,
    description: str,
    salary: Decimal,
    location: str,
    skills: list[str],
    company_id: int,
    current_user: models.User,
    employment_type: str = "Full-time",
    experience_level: str = "Entry",
    work_mode: str = "Onsite"
):
    title = title.strip()
    description = description.strip()
    location = location.strip()

    cleaned_skills = [
        skill.strip().lower()
        for skill in skills
        if skill and skill.strip()
    ]

    if not title:
        raise HTTPException(status_code=400, detail="Job title cannot be empty")
    if not description:
        raise HTTPException(status_code=400, detail="Job description cannot be empty")
    if not location:
        raise HTTPException(status_code=400, detail="Job location cannot be empty")
    if not cleaned_skills:
        raise HTTPException(status_code=400, detail="At least one valid skill is required")

    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    # Ownership Guard: Must own company to post jobs
    if current_user.role.lower() != "admin" and company.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only create jobs for companies you own"
        )

    new_job = models.Job(
        title=title,
        description=description,
        salary=salary,
        location=location,
        skills=list(dict.fromkeys(cleaned_skills)),
        company_id=company_id,
        employment_type=employment_type,
        experience_level=experience_level,
        work_mode=work_mode
    )

    db.add(new_job)

    try:
        db.commit()
        db.refresh(new_job)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Another job with this title already exists for this company"
        )

    return new_job


def update_job(
    db: Session,
    job_id: int,
    job_data,
    current_user: models.User
):
    job = (
        db.query(models.Job)
        .options(joinedload(models.Job.company))
        .filter(models.Job.id == job_id)
        .first()
    )

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Ownership Guard: Must own company to update job
    if current_user.role.lower() != "admin" and job.company.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to update this job"
        )

    update_data = job_data.model_dump(exclude_unset=True)

    if "title" in update_data:
        update_data["title"] = update_data["title"].strip()
        if not update_data["title"]:
            raise HTTPException(status_code=400, detail="Job title cannot be empty")

    if "description" in update_data:
        update_data["description"] = update_data["description"].strip()
        if not update_data["description"]:
            raise HTTPException(status_code=400, detail="Job description cannot be empty")

    if "location" in update_data:
        update_data["location"] = update_data["location"].strip()
        if not update_data["location"]:
            raise HTTPException(status_code=400, detail="Job location cannot be empty")

    if "skills" in update_data:
        cleaned_skills = [
            skill.strip().lower()
            for skill in update_data["skills"]
            if skill and skill.strip()
        ]
        if not cleaned_skills:
            raise HTTPException(status_code=400, detail="At least one valid skill is required")

        update_data["skills"] = list(dict.fromkeys(cleaned_skills))

    # Safely convert Enums if passed as Enum instances
    for enum_field in ["employment_type", "experience_level", "work_mode"]:
        if enum_field in update_data:
            val = update_data[enum_field]
            update_data[enum_field] = getattr(val, "value", val)

    for key, value in update_data.items():
        setattr(job, key, value)

    try:
        db.commit()
        db.refresh(job)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Another job with this title already exists for this company"
        )

    return job


def delete_job(
    db: Session,
    job_id: int,
    current_user: models.User
):
    job = (
        db.query(models.Job)
        .options(joinedload(models.Job.company))
        .filter(models.Job.id == job_id)
        .first()
    )

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Ownership Guard: Must own company to delete job
    if current_user.role.lower() != "admin" and job.company.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to delete this job"
        )

    # Prevent deletion if applications exist
    application_exists = (
        db.query(models.Application)
        .filter(models.Application.job_id == job_id)
        .first()
    )

    if application_exists is not None:
        raise HTTPException(
            status_code=409,
            detail="Job cannot be deleted because applications exist for this job"
        )

    try:
        db.delete(job)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Job cannot be deleted because of a database constraint"
        )

    return {"message": "Job deleted successfully!"}