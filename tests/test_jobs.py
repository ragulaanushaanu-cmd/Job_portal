from datetime import date

from auth import hash_password
import models


def create_test_user(
    db,
    username: str,
    email: str,
    role: str,
):
    user = models.User(
        username=username,
        email=email,
        password=hash_password("TestPassword123"),
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
            "password": "TestPassword123",
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
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    return response.json()


def test_job_crud_and_authorization(client, db):
    employer = create_test_user(
        db,
        "job_employer",
        "job_employer@example.com",
        "Employer",
    )

    candidate = create_test_user(
        db,
        "job_candidate",
        "job_candidate@example.com",
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
        "Test Job Company",
    )

    company_id = company["id"]

    create_response = client.post(
        "/jobs/",
        json={
            "title": "Backend Developer",
            "description": "Python backend development",
            "location": "Hyderabad",
            "skills": ["Python", "FastAPI"],
            "company_id": company_id,
            "salary": 60000,
            "employment_type": "Full-time",
            "experience_level": "Entry",
            "work_mode": "Onsite",
        },
        headers={"Authorization": f"Bearer {employer_token}"},
    )

    assert create_response.status_code == 201

    job = create_response.json()
    job_id = job["id"]

    assert job["title"] == "Backend Developer"
    assert job["company_id"] == company_id

    get_response = client.get(
        f"/jobs/{job_id}",
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == job_id

    update_response = client.put(
        f"/jobs/{job_id}",
        json={
            "title": "Senior Backend Developer",
            "description": "Updated backend development role",
            "location": "Hyderabad",
            "skills": ["Python", "FastAPI", "SQL"],
            "company_id": company_id,
            "salary": 75000,
            "employment_type": "Full-time",
            "experience_level": "Entry",
            "work_mode": "Hybrid",
        },
        headers={"Authorization": f"Bearer {employer_token}"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Senior Backend Developer"

    candidate_update_response = client.put(
        f"/jobs/{job_id}",
        json={
            "title": "Unauthorized Update",
            "description": "Should fail",
            "location": "Hyderabad",
            "skills": ["Python"],
            "company_id": company_id,
            "salary": 50000,
            "employment_type": "Full-time",
            "experience_level": "Entry",
            "work_mode": "Onsite",
        },
        headers={"Authorization": f"Bearer {candidate_token}"},
    )

    assert candidate_update_response.status_code == 403

    list_response = client.get("/jobs/")

    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1

    delete_response = client.delete(
        f"/jobs/{job_id}",
        headers={"Authorization": f"Bearer {employer_token}"},
    )

    assert delete_response.status_code == 204

    get_deleted_response = client.get(
        f"/jobs/{job_id}",
    )

    assert get_deleted_response.status_code == 404