from datetime import date

from auth import hash_password
import models


TEST_PASSWORD = "TestPassword123"


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


def create_company(client, token, name="Application Test Company"):
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


def create_job(client, token, company_id):
    response = client.post(
        "/jobs/",
        json={
            "title": "Backend Developer",
            "description": "Python backend development role for testing",
            "salary": 60000,
            "location": "Hyderabad",
            "skills": [
                "Python",
                "FastAPI",
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


def create_resume_directly(db, candidate_id):
    resume = models.Resume(
        user_id=candidate_id,
        original_filename="test_resume.pdf",
        stored_filename=f"test_resume_application_test_{candidate_id}.pdf",
        file_type="application/pdf",
        file_size=1024,
        file_path=f"test_resumes/test_resume_application_test_{candidate_id}.pdf",
        is_primary=True,
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    return resume


def test_application_create_and_access_control(client, db):
    employer = create_test_user(
        db,
        "application_employer",
        "application_employer@example.com",
        "Employer",
    )

    candidate = create_test_user(
        db,
        "application_candidate",
        "application_candidate@example.com",
        "Candidate",
    )

    other_candidate = create_test_user(
        db,
        "application_other_candidate",
        "application_other_candidate@example.com",
        "Candidate",
    )

    employer_token = get_access_token(
        client,
        employer.email,
    )

    candidate_token = get_access_token(
        client,
        candidate.email,
    )

    other_candidate_token = get_access_token(
        client,
        other_candidate.email,
    )

    company = create_company(
        client,
        employer_token,
    )

    job = create_job(
        client,
        employer_token,
        company["id"],
    )

    resume = create_resume_directly(
        db,
        candidate.id,
    )

    application_response = client.post(
        "/applications/",
        json={
            "job_id": job["id"],
            "resume_id": resume.id,
        },
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert application_response.status_code == 201

    application = application_response.json()

    application_id = application["id"]

    assert application["user_id"] == candidate.id
    assert application["job_id"] == job["id"]
    assert application["resume_id"] == resume.id
    assert application["status"] == "Applied"

    my_applications_response = client.get(
        "/applications/",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert my_applications_response.status_code == 200

    my_applications = my_applications_response.json()

    assert my_applications["total"] == 1
    assert len(my_applications["items"]) == 1
    assert my_applications["items"][0]["id"] == application_id

    other_candidate_response = client.get(
        "/applications/",
        headers={
            "Authorization": f"Bearer {other_candidate_token}",
        },
    )

    assert other_candidate_response.status_code == 200

    other_candidate_applications = other_candidate_response.json()

    assert other_candidate_applications["total"] == 0


def test_application_details_history_and_status_update(
    client,
    db,
):
    employer = create_test_user(
        db,
        "application_status_employer",
        "application_status_employer@example.com",
        "Employer",
    )

    candidate = create_test_user(
        db,
        "application_status_candidate",
        "application_status_candidate@example.com",
        "Candidate",
    )

    employer_token = get_access_token(
        client,
        employer.email,
    )

    candidate_token = get_access_token(
        client,
        candidate.email,
    )

    company = create_company(
        client,
        employer_token,
        "Application Status Company",
    )

    job = create_job(
        client,
        employer_token,
        company["id"],
    )

    resume = create_resume_directly(
        db,
        candidate.id,
    )

    application_response = client.post(
        "/applications/",
        json={
            "job_id": job["id"],
            "resume_id": resume.id,
        },
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert application_response.status_code == 201

    application_id = application_response.json()["id"]

    details_response = client.get(
        f"/applications/{application_id}",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert details_response.status_code == 200

    details = details_response.json()

    assert details["id"] == application_id
    assert details["status"] == "Applied"
    assert details["user"]["id"] == candidate.id
    assert details["job"]["id"] == job["id"]
    assert details["resume"]["id"] == resume.id

    employer_status_response = client.put(
        f"/applications/{application_id}",
        json={
            "status": "Shortlisted",
        },
        headers={
            "Authorization": f"Bearer {employer_token}",
        },
    )

    assert employer_status_response.status_code == 200

    updated_application = employer_status_response.json()

    assert updated_application["status"] == "Shortlisted"

    history_response = client.get(
        f"/applications/{application_id}/history",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert len(history) >= 2

    assert history[0]["new_status"] == "Applied"
    assert history[-1]["new_status"] == "Shortlisted"


def test_application_role_restrictions(client, db):
    candidate = create_test_user(
        db,
        "application_restricted_candidate",
        "application_restricted_candidate@example.com",
        "Candidate",
    )

    employer = create_test_user(
        db,
        "application_restricted_employer",
        "application_restricted_employer@example.com",
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

    candidate_employer_response = client.get(
        "/applications/employer",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert candidate_employer_response.status_code == 403

    employer_my_applications_response = client.get(
        "/applications/",
        headers={
            "Authorization": f"Bearer {employer_token}",
        },
    )

    assert employer_my_applications_response.status_code == 403