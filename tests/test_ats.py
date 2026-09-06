from datetime import date

from auth import hash_password
import models


TEST_PASSWORD = "TestPassword123"
PARSER_VERSION = "2.8"


def create_test_user(
    db,
    username: str,
    email: str,
    role: str,
):
    user = models.User(
        username=username,
        email=email,
        password=hash_password(TEST_PASSWORD),
        date_of_birth=date(2000, 1, 1),
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_access_token(client, email: str):
    response = client.post(
        "/login",
        data={
            "username": email,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def create_company(client, token, name):
    response = client.post(
        "/companies/",
        json={
            "name": name,
            "location": "Hyderabad",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_job(client, token, company_id, title="Backend Developer"):
    response = client.post(
        "/jobs/",
        json={
            "title": title,
            "description": (
                "Python FastAPI backend development role "
                "requiring REST API development and SQL."
            ),
            "salary": 60000,
            "location": "Hyderabad",
            "skills": [
                "Python",
                "FastAPI",
                "SQL",
            ],
            "company_id": company_id,
            "employment_type": "Full-time",
            "experience_level": "Entry",
            "work_mode": "Onsite",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_resume_with_parsed_data(
    db,
    candidate_id,
    suffix,
    parser_version=PARSER_VERSION,
    status="Completed",
):
    resume = models.Resume(
        user_id=candidate_id,
        original_filename=f"ats_resume_{suffix}.pdf",
        stored_filename=f"ats_resume_{suffix}.pdf",
        file_type="application/pdf",
        file_size=1024,
        file_path=f"test_resumes/ats_resume_{suffix}.pdf",
        is_primary=True,
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    parsing_result = models.ResumeParsingResult(
        resume_id=resume.id,
        status=status,
        extracted_text=(
            "Backend Developer Python FastAPI SQL REST API "
            "software development unit testing"
        ),
        parsed_data={
            "personal": {
                "name": "ATS Test Candidate",
            },
            "skills": [
                "Python",
                "Fast API",
                "sql",
                "REST APIs",
            ],
            "education": [
                {
                    "degree": "B.Tech",
                    "institution": "Test University",
                    "details": [],
                }
            ],
            "experience": [
                {
                    "title": "Backend Developer",
                    "company": "Test Company",
                    "description": [
                        "Developed Python FastAPI backend APIs."
                    ],
                }
            ],
            "projects": [
                {
                    "name": "Job Portal",
                    "technologies": [
                        "Python",
                        "FastAPI",
                        "SQL",
                    ],
                    "description": [
                        "Built REST API backend application."
                    ],
                }
            ],
        },
        parser_version=parser_version,
    )

    db.add(parsing_result)
    db.commit()
    db.refresh(resume)

    return resume


def test_ats_analysis_create_and_retrieve(
    client,
    db,
):
    candidate = create_test_user(
        db,
        "ats_candidate",
        "ats_candidate@example.com",
        "Candidate",
    )

    employer = create_test_user(
        db,
        "ats_employer",
        "ats_employer@example.com",
        "Employer",
    )

    candidate_token = get_access_token(
        client,
        candidate.email,
    )

    employer_token = get_access_token(
        client,
        employer.email,
    )

    company = create_company(
        client,
        employer_token,
        "ATS Test Company",
    )

    job = create_job(
        client,
        employer_token,
        company["id"],
    )

    resume = create_resume_with_parsed_data(
        db,
        candidate.id,
        "create_retrieve",
    )

    analyze_response = client.post(
        f"/ats/analyze/{resume.id}/{job['id']}",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert analyze_response.status_code == 200

    analysis = analyze_response.json()

    analysis_id = analysis["id"]

    assert analysis["resume_id"] == resume.id
    assert analysis["job_id"] == job["id"]

    assert 0 <= float(analysis["overall_score"]) <= 100
    assert 0 <= float(analysis["skill_score"]) <= 100
    assert 0 <= float(analysis["experience_score"]) <= 100
    assert 0 <= float(analysis["education_score"]) <= 100
    assert 0 <= float(analysis["keyword_score"]) <= 100

    assert isinstance(analysis["matched_skills"], list)
    assert isinstance(analysis["missing_skills"], list)
    assert isinstance(analysis["matched_keywords"], list)
    assert isinstance(analysis["missing_keywords"], list)
    assert isinstance(analysis["recommendations"], list)

    assert "python" in analysis["matched_skills"]
    assert "fastapi" in analysis["matched_skills"]
    assert "sql" in analysis["matched_skills"]

    get_response = client.get(
        f"/ats/{analysis_id}",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert get_response.status_code == 200

    retrieved = get_response.json()

    assert retrieved["id"] == analysis_id
    assert retrieved["resume_id"] == resume.id
    assert retrieved["job_id"] == job["id"]


def test_ats_rerun_updates_existing_analysis(
    client,
    db,
):
    candidate = create_test_user(
        db,
        "ats_rerun_candidate",
        "ats_rerun_candidate@example.com",
        "Candidate",
    )

    employer = create_test_user(
        db,
        "ats_rerun_employer",
        "ats_rerun_employer@example.com",
        "Employer",
    )

    candidate_token = get_access_token(
        client,
        candidate.email,
    )

    employer_token = get_access_token(
        client,
        employer.email,
    )

    company = create_company(
        client,
        employer_token,
        "ATS Rerun Company",
    )

    job = create_job(
        client,
        employer_token,
        company["id"],
        "ATS Rerun Backend Developer",
    )

    resume = create_resume_with_parsed_data(
        db,
        candidate.id,
        "rerun",
    )

    first_response = client.post(
        f"/ats/analyze/{resume.id}/{job['id']}",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert first_response.status_code == 200

    first_analysis = first_response.json()

    second_response = client.post(
        f"/ats/analyze/{resume.id}/{job['id']}",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert second_response.status_code == 200

    second_analysis = second_response.json()

    assert second_analysis["id"] == first_analysis["id"]
    assert second_analysis["resume_id"] == resume.id
    assert second_analysis["job_id"] == job["id"]

    pair_response = client.get(
        f"/ats/resume/{resume.id}/job/{job['id']}",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert pair_response.status_code == 200

    pair_analysis = pair_response.json()

    assert pair_analysis["id"] == first_analysis["id"]

    analysis_rows = (
        db.query(models.ATSAnalysis)
        .filter(
            models.ATSAnalysis.resume_id == resume.id,
            models.ATSAnalysis.job_id == job["id"],
        )
        .all()
    )

    assert len(analysis_rows) == 1


def test_ats_resume_ownership_and_role_restriction(
    client,
    db,
):
    candidate_one = create_test_user(
        db,
        "ats_owner_candidate",
        "ats_owner_candidate@example.com",
        "Candidate",
    )

    candidate_two = create_test_user(
        db,
        "ats_other_candidate",
        "ats_other_candidate@example.com",
        "Candidate",
    )

    employer = create_test_user(
        db,
        "ats_role_employer",
        "ats_role_employer@example.com",
        "Employer",
    )

    candidate_one_token = get_access_token(
        client,
        candidate_one.email,
    )

    candidate_two_token = get_access_token(
        client,
        candidate_two.email,
    )

    employer_token = get_access_token(
        client,
        employer.email,
    )

    company = create_company(
        client,
        employer_token,
        "ATS Ownership Company",
    )

    job = create_job(
        client,
        employer_token,
        company["id"],
        "ATS Ownership Developer",
    )

    resume = create_resume_with_parsed_data(
        db,
        candidate_one.id,
        "ownership",
    )

    owner_analysis_response = client.post(
        f"/ats/analyze/{resume.id}/{job['id']}",
        headers={
            "Authorization": f"Bearer {candidate_one_token}",
        },
    )

    assert owner_analysis_response.status_code == 200

    analysis_id = owner_analysis_response.json()["id"]

    other_candidate_response = client.get(
        f"/ats/{analysis_id}",
        headers={
            "Authorization": f"Bearer {candidate_two_token}",
        },
    )

    assert other_candidate_response.status_code == 403

    other_candidate_pair_response = client.get(
        f"/ats/resume/{resume.id}/job/{job['id']}",
        headers={
            "Authorization": f"Bearer {candidate_two_token}",
        },
    )

    assert other_candidate_pair_response.status_code == 403

    other_candidate_analyze_response = client.post(
        f"/ats/analyze/{resume.id}/{job['id']}",
        headers={
            "Authorization": f"Bearer {candidate_two_token}",
        },
    )

    assert other_candidate_analyze_response.status_code == 403

    employer_analyze_response = client.post(
        f"/ats/analyze/{resume.id}/{job['id']}",
        headers={
            "Authorization": f"Bearer {employer_token}",
        },
    )

    assert employer_analyze_response.status_code == 403


def test_ats_parser_readiness_validation(
    client,
    db,
):
    candidate = create_test_user(
        db,
        "ats_parser_candidate",
        "ats_parser_candidate@example.com",
        "Candidate",
    )

    employer = create_test_user(
        db,
        "ats_parser_employer",
        "ats_parser_employer@example.com",
        "Employer",
    )

    candidate_token = get_access_token(
        client,
        candidate.email,
    )

    employer_token = get_access_token(
        client,
        employer.email,
    )

    company = create_company(
        client,
        employer_token,
        "ATS Parser Company",
    )

    job = create_job(
        client,
        employer_token,
        company["id"],
        "ATS Parser Developer",
    )

    incomplete_resume = create_resume_with_parsed_data(
        db,
        candidate.id,
        "incomplete",
        parser_version=PARSER_VERSION,
        status="Pending",
    )

    incomplete_response = client.post(
        f"/ats/analyze/{incomplete_resume.id}/{job['id']}",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert incomplete_response.status_code == 409

    bad_version_resume = create_resume_with_parsed_data(
        db,
        candidate.id,
        "bad_version",
        parser_version="1.0",
        status="Completed",
    )

    bad_version_response = client.post(
        f"/ats/analyze/{bad_version_resume.id}/{job['id']}",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert bad_version_response.status_code == 409

    missing_resume_response = client.post(
        "/ats/analyze/999999/999999",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert missing_resume_response.status_code == 404
    