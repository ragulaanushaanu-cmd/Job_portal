from datetime import date

from auth import hash_password


TEST_PASSWORD = "TestPassword123"


def create_test_user(
    db,
    username: str,
    email: str,
    role: str,
):
    import models

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
            "description": "Python backend development role for dashboard testing",
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


def upload_test_resume(client, token, filename):
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog /Pages 2 0 R >>\n"
        b"endobj\n"
        b"2 0 obj\n"
        b"<< /Type /Pages /Kids [] /Count 0 >>\n"
        b"endobj\n"
        b"trailer\n"
        b"<< /Root 1 0 R >>\n"
        b"%%EOF"
    )

    response = client.post(
        "/resumes/upload",
        files={
            "file": (
                filename,
                pdf_content,
                "application/pdf",
            )
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 201

    return response.json()


def test_candidate_dashboard_aggregates_data(
    client,
    db,
):
    candidate = create_test_user(
        db,
        "dashboard_candidate",
        "dashboard_candidate@example.com",
        "Candidate",
    )

    employer = create_test_user(
        db,
        "dashboard_employer",
        "dashboard_employer@example.com",
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

    # -------------------------
    # PROFILE
    # -------------------------

    profile_response = client.post(
        "/candidate-profile/",
        json={
            "headline": "Backend Developer",
            "location": "Hyderabad",
            "skills": [
                "Python",
                "FastAPI",
                "SQL",
            ],
        },
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert profile_response.status_code == 201

    # -------------------------
    # RESUMES
    # -------------------------

    resume = upload_test_resume(
        client,
        candidate_token,
        "dashboard_resume.pdf",
    )

    # -------------------------
    # COMPANY + JOBS
    # -------------------------

    company = create_company(
        client,
        employer_token,
        "Dashboard Test Company",
    )

    job_one = create_job(
        client,
        employer_token,
        company["id"],
        "Dashboard Backend Developer",
    )

    job_two = create_job(
        client,
        employer_token,
        company["id"],
        "Dashboard Python Developer",
    )

    # -------------------------
    # APPLICATION
    # -------------------------

    application_response = client.post(
        "/applications/",
        json={
            "job_id": job_one["id"],
            "resume_id": resume["id"],
        },
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert application_response.status_code == 201

    application = application_response.json()

    # -------------------------
    # SAVE ANOTHER JOB
    # -------------------------

    saved_job_response = client.post(
        f"/saved-jobs/{job_two['id']}",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert saved_job_response.status_code == 201

    # -------------------------
    # DASHBOARD
    # -------------------------

    dashboard_response = client.get(
        "/candidate/dashboard",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert dashboard_response.status_code == 200

    dashboard = dashboard_response.json()

    # -------------------------
    # PROFILE
    # -------------------------

    assert dashboard["profile"] is not None
    assert dashboard["profile"]["headline"] == "Backend Developer"
    assert dashboard["profile"]["location"] == "Hyderabad"
    assert dashboard["profile"]["skills"] == [
        "Python",
        "FastAPI",
        "SQL",
    ]

    # -------------------------
    # RESUMES
    # -------------------------

    assert dashboard["resumes"]["total"] == 1
    assert dashboard["resumes"]["primary_resume_id"] == resume["id"]

    # -------------------------
    # APPLICATION COUNTS
    # -------------------------

    assert dashboard["applications"]["total"] == 1
    assert dashboard["applications"]["applied"] == 1
    assert dashboard["applications"]["shortlisted"] == 0
    assert dashboard["applications"]["rejected"] == 0
    assert dashboard["applications"]["selected"] == 0

    # -------------------------
    # SAVED JOBS
    # -------------------------

    assert dashboard["saved_jobs"]["total"] == 1

    # -------------------------
    # RECENT APPLICATIONS
    # -------------------------

    assert len(dashboard["recent_applications"]) == 1

    recent = dashboard["recent_applications"][0]

    assert recent["application_id"] == application["id"]
    assert recent["job_id"] == job_one["id"]
    assert recent["job_title"] == job_one["title"]
    assert recent["company_name"] == company["name"]
    assert recent["status"] == "Applied"

    # -------------------------
    # STATUS UPDATE
    # -------------------------

    update_response = client.put(
        f"/applications/{application['id']}",
        json={
            "status": "Shortlisted",
        },
        headers={
            "Authorization": f"Bearer {employer_token}",
        },
    )

    assert update_response.status_code == 200

    dashboard_after_update = client.get(
        "/candidate/dashboard",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert dashboard_after_update.status_code == 200

    updated_dashboard = dashboard_after_update.json()

    assert updated_dashboard["applications"]["total"] == 1
    assert updated_dashboard["applications"]["applied"] == 0
    assert updated_dashboard["applications"]["shortlisted"] == 1
    assert updated_dashboard["applications"]["rejected"] == 0
    assert updated_dashboard["applications"]["selected"] == 0

    assert (
        updated_dashboard["recent_applications"][0]["status"]
        == "Shortlisted"
    )


def test_candidate_dashboard_role_restriction(client, db):
    employer = create_test_user(
        db,
        "dashboard_restricted_employer",
        "dashboard_restricted_employer@example.com",
        "Employer",
    )

    admin = create_test_user(
        db,
        "dashboard_restricted_admin",
        "dashboard_restricted_admin@example.com",
        "Admin",
    )

    employer_token = get_access_token(
        client,
        employer.email,
    )

    admin_token = get_access_token(
        client,
        admin.email,
    )

    employer_response = client.get(
        "/candidate/dashboard",
        headers={
            "Authorization": f"Bearer {employer_token}",
        },
    )

    assert employer_response.status_code == 403

    admin_response = client.get(
        "/candidate/dashboard",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert admin_response.status_code == 403