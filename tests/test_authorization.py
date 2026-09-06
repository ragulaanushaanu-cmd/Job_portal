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


def test_role_based_access(client, db):
    candidate = create_test_user(
        db,
        "candidate_rbac",
        "candidate_rbac@example.com",
        "Candidate",
    )

    employer = create_test_user(
        db,
        "employer_rbac",
        "employer_rbac@example.com",
        "Employer",
    )

    admin = create_test_user(
        db,
        "admin_rbac",
        "admin_rbac@example.com",
        "Admin",
    )

    candidate_token = get_access_token(
        client,
        candidate.email,
    )

    employer_token = get_access_token(
        client,
        employer.email,
    )

    admin_token = get_access_token(
        client,
        admin.email,
    )

    # Candidate can access candidate dashboard
    response = client.get(
        "/candidate/dashboard",
        headers={
            "Authorization": f"Bearer {candidate_token}"
        },
    )

    assert response.status_code == 200

    # Candidate cannot access employer dashboard
    response = client.get(
        "/employer/dashboard",
        headers={
            "Authorization": f"Bearer {candidate_token}"
        },
    )

    assert response.status_code == 403

    # Employer can access employer dashboard
    response = client.get(
        "/employer/dashboard",
        headers={
            "Authorization": f"Bearer {employer_token}"
        },
    )

    assert response.status_code == 200

    # Employer cannot access candidate dashboard
    response = client.get(
        "/candidate/dashboard",
        headers={
            "Authorization": f"Bearer {employer_token}"
        },
    )

    assert response.status_code == 403

    # Admin can access admin-only user listing
    response = client.get(
        "/users/",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    # Candidate cannot access admin-only user listing
    response = client.get(
        "/users/",
        headers={
            "Authorization": f"Bearer {candidate_token}"
        },
    )

    assert response.status_code == 403