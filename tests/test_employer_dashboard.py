from datetime import date
from auth import hash_password
import models

TEST_PASSWORD = "TestPassword123"

def create_test_user(db, username: str, email: str, role: str):
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
            "description": "Backend development role for employer dashboard testing",
            "salary": 60000,
            "location": "Hyderabad",
            "skills": ["Python", "FastAPI"],
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

def create_application(client, candidate_token, job_id, resume_id):
    response = client.post(
        "/applications/",
        json={
            "job_id": job_id,
            "resume_id": resume_id,
        },
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )
    assert response.status_code == 201
    return response.json()

def update_application_status(client, employer_token, application_id, status_value):
    response = client.put(
        f"/applications/{application_id}",
        json={
            "status": status_value,
        },
        headers={
            "Authorization": f"Bearer {employer_token}",
        },
    )
    return response

def test_employer_dashboard_aggregates_owned_company_data(client, db):
    employer = create_test_user(
        db, "employer_dashboard_owner", "employer_dashboard_owner@example.com", "Employer"
    )
    candidate_one = create_test_user(
        db, "employer_dashboard_candidate_one", "employer_dashboard_candidate_one@example.com", "Candidate"
    )
    candidate_two = create_test_user(
        db, "employer_dashboard_candidate_two", "employer_dashboard_candidate_two@example.com", "Candidate"
    )

    employer_token = get_access_token(client, employer.email)
    candidate_one_token = get_access_token(client, candidate_one.email)
    candidate_two_token = get_access_token(client, candidate_two.email)

    company_one = create_company(client, employer_token, "Employer Dashboard Company One")
    company_two = create_company(client, employer_token, "Employer Dashboard Company Two")

    job_one = create_job(client, employer_token, company_one["id"], "Dashboard Backend Developer")
    job_two = create_job(client, employer_token, company_two["id"], "Dashboard Python Developer")

    resume_one = upload_test_resume(client, candidate_one_token, "employer_dashboard_resume_one.pdf")
    resume_two = upload_test_resume(client, candidate_two_token, "employer_dashboard_resume_two.pdf")

    application_one = create_application(client, candidate_one_token, job_one["id"], resume_one["id"])
    application_two = create_application(client, candidate_two_token, job_two["id"], resume_two["id"])

    res1 = update_application_status(client, employer_token, application_one["id"], "Shortlisted")
    assert res1.status_code == 200

    res2 = update_application_status(client, employer_token, application_two["id"], "Shortlisted")
    assert res2.status_code == 200

    res2_select = update_application_status(client, employer_token, application_two["id"], "Selected")
    if res2_select.status_code != 200:
        res2_select = update_application_status(client, employer_token, application_two["id"], "Rejected")
    assert res2_select.status_code == 200

    dashboard_response = client.get(
        "/employer/dashboard",
        headers={
            "Authorization": f"Bearer {employer_token}",
        },
    )
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()

    assert len(dashboard["companies"]) == 2
    company_ids = {company["id"] for company in dashboard["companies"]}
    assert company_one["id"] in company_ids
    assert company_two["id"] in company_ids

    assert dashboard["total_jobs"] == 2
    assert dashboard["applications"]["total"] == 2
    assert dashboard["applications"]["applied"] == 0

    assert len(dashboard["recent_applications"]) == 2
    recent_application_ids = {app["application_id"] for app in dashboard["recent_applications"]}
    assert application_one["id"] in recent_application_ids
    assert application_two["id"] in recent_application_ids

    recent_by_id = {app["application_id"]: app for app in dashboard["recent_applications"]}
    assert recent_by_id[application_one["id"]]["candidate_name"] == candidate_one.username
    assert recent_by_id[application_two["id"]]["candidate_name"] == candidate_two.username

def test_employer_dashboard_is_role_restricted(client, db):
    employer = create_test_user(
        db, "dashboard_role_employer", "dashboard_role_employer@example.com", "Employer"
    )
    candidate = create_test_user(
        db, "dashboard_role_candidate", "dashboard_role_candidate@example.com", "Candidate"
    )
    admin = create_test_user(
        db, "dashboard_role_admin", "dashboard_role_admin@example.com", "Admin"
    )

    employer_token = get_access_token(client, employer.email)
    candidate_token = get_access_token(client, candidate.email)
    admin_token = get_access_token(client, admin.email)

    employer_response = client.get(
        "/employer/dashboard",
        headers={
            "Authorization": f"Bearer {employer_token}",
        },
    )
    assert employer_response.status_code == 200

    candidate_response = client.get(
        "/employer/dashboard",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )
    assert candidate_response.status_code == 403

    admin_response = client.get(
        "/employer/dashboard",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )
    assert admin_response.status_code == 200
