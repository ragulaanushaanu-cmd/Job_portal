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


def create_job(client, token, company_id, title):
    response = client.post(
        "/jobs/",
        json={
            "title": title,
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


def test_save_list_and_remove_job(client, db):
    employer = create_test_user(
        db,
        "saved_job_employer",
        "saved_job_employer@example.com",
        "Employer",
    )

    candidate = create_test_user(
        db,
        "saved_job_candidate",
        "saved_job_candidate@example.com",
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
        "Saved Job Test Company",
    )

    job_one = create_job(
        client,
        employer_token,
        company["id"],
        "Backend Developer",
    )

    job_two = create_job(
        client,
        employer_token,
        company["id"],
        "Python Developer",
    )

    save_one_response = client.post(
        f"/saved-jobs/{job_one['id']}",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert save_one_response.status_code == 201

    saved_one = save_one_response.json()

    assert saved_one["job_id"] == job_one["id"]
    assert "saved_at" in saved_one

    save_two_response = client.post(
        f"/saved-jobs/{job_two['id']}",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert save_two_response.status_code == 201

    saved_jobs_response = client.get(
        "/saved-jobs/",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert saved_jobs_response.status_code == 200

    saved_jobs = saved_jobs_response.json()

    assert saved_jobs["total"] == 2
    assert len(saved_jobs["items"]) == 2

    saved_job_ids = {
        item["job"]["id"]
        for item in saved_jobs["items"]
    }

    assert job_one["id"] in saved_job_ids
    assert job_two["id"] in saved_job_ids

    first_saved_job = next(
        item
        for item in saved_jobs["items"]
        if item["job"]["id"] == job_one["id"]
    )

    assert first_saved_job["job"]["title"] == "Backend Developer"
    assert first_saved_job["job"]["location"] == "Hyderabad"
    assert first_saved_job["job"]["company"]["id"] == company["id"]
    assert first_saved_job["job"]["company"]["name"] == company["name"]

    duplicate_response = client.post(
        f"/saved-jobs/{job_one['id']}",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert duplicate_response.status_code == 409

    delete_response = client.delete(
        f"/saved-jobs/{job_one['id']}",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert delete_response.status_code == 204

    remaining_response = client.get(
        "/saved-jobs/",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert remaining_response.status_code == 200

    remaining_saved_jobs = remaining_response.json()

    assert remaining_saved_jobs["total"] == 1
    assert remaining_saved_jobs["items"][0]["job"]["id"] == job_two["id"]


def test_saved_job_ownership_and_missing_job(
    client,
    db,
):
    employer = create_test_user(
        db,
        "saved_job_owner_employer",
        "saved_job_owner_employer@example.com",
        "Employer",
    )

    candidate_one = create_test_user(
        db,
        "saved_job_owner_candidate",
        "saved_job_owner_candidate@example.com",
        "Candidate",
    )

    candidate_two = create_test_user(
        db,
        "saved_job_other_candidate",
        "saved_job_other_candidate@example.com",
        "Candidate",
    )

    employer_token = get_access_token(
        client,
        employer.email,
    )

    candidate_one_token = get_access_token(
        client,
        candidate_one.email,
    )

    candidate_two_token = get_access_token(
        client,
        candidate_two.email,
    )

    company = create_company(
        client,
        employer_token,
        "Saved Job Ownership Company",
    )

    job = create_job(
        client,
        employer_token,
        company["id"],
        "Ownership Test Developer",
    )

    save_response = client.post(
        f"/saved-jobs/{job['id']}",
        headers={
            "Authorization": f"Bearer {candidate_one_token}",
        },
    )

    assert save_response.status_code == 201

    candidate_two_delete_response = client.delete(
        f"/saved-jobs/{job['id']}",
        headers={
            "Authorization": f"Bearer {candidate_two_token}",
        },
    )

    assert candidate_two_delete_response.status_code == 404

    candidate_one_saved_jobs = client.get(
        "/saved-jobs/",
        headers={
            "Authorization": f"Bearer {candidate_one_token}",
        },
    )

    assert candidate_one_saved_jobs.status_code == 200
    assert candidate_one_saved_jobs.json()["total"] == 1

    missing_job_response = client.post(
        "/saved-jobs/999999",
        headers={
            "Authorization": f"Bearer {candidate_one_token}",
        },
    )

    assert missing_job_response.status_code == 404