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


def test_resume_upload_list_download_primary_and_delete(
    client,
    db,
):
    candidate = create_test_user(
        db,
        "resume_candidate",
        "resume_candidate@example.com",
        "Candidate",
    )

    candidate_token = get_access_token(
        client,
        candidate.email,
    )

    resume_one = upload_test_resume(
        client,
        candidate_token,
        "resume_one.pdf",
    )

    resume_two = upload_test_resume(
        client,
        candidate_token,
        "resume_two.pdf",
    )

    assert resume_one["user_id"] == candidate.id
    assert resume_one["original_filename"] == "resume_one.pdf"

    assert resume_two["user_id"] == candidate.id
    assert resume_two["original_filename"] == "resume_two.pdf"

    resume_list_response = client.get(
        "/resumes/",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert resume_list_response.status_code == 200

    resumes = resume_list_response.json()

    assert len(resumes) >= 2

    resume_ids = {resume["id"] for resume in resumes}

    assert resume_one["id"] in resume_ids
    assert resume_two["id"] in resume_ids

    download_response = client.get(
        f"/resumes/{resume_one['id']}/download",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert download_response.status_code == 200

    set_primary_response = client.put(
        f"/resumes/{resume_two['id']}/primary",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert set_primary_response.status_code == 200

    primary_resume = set_primary_response.json()

    assert primary_resume["id"] == resume_two["id"]
    assert primary_resume["is_primary"] is True

    delete_response = client.delete(
        f"/resumes/{resume_one['id']}",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert delete_response.status_code == 200

    remaining_resumes_response = client.get(
        "/resumes/",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert remaining_resumes_response.status_code == 200

    remaining_resumes = remaining_resumes_response.json()

    remaining_ids = {
        resume["id"] for resume in remaining_resumes
    }

    assert resume_one["id"] not in remaining_ids
    assert resume_two["id"] in remaining_ids


def test_resume_role_restrictions(client, db):
    candidate = create_test_user(
        db,
        "resume_restricted_candidate",
        "resume_restricted_candidate@example.com",
        "Candidate",
    )

    employer = create_test_user(
        db,
        "resume_restricted_employer",
        "resume_restricted_employer@example.com",
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

    employer_list_response = client.get(
        "/resumes/",
        headers={
            "Authorization": f"Bearer {employer_token}",
        },
    )

    assert employer_list_response.status_code == 403

    employer_upload_response = client.post(
        "/resumes/upload",
        files={
            "file": (
                "employer_resume.pdf",
                b"%PDF-1.4\n%%EOF",
                "application/pdf",
            )
        },
        headers={
            "Authorization": f"Bearer {employer_token}",
        },
    )

    assert employer_upload_response.status_code == 403

    candidate_list_response = client.get(
        "/resumes/",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert candidate_list_response.status_code == 200