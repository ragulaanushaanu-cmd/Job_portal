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


def test_profile_create_get_update_delete(client, db):
    candidate = create_test_user(
        db,
        "profile_candidate",
        "profile_candidate@example.com",
        "Candidate",
    )

    candidate_token = get_access_token(
        client,
        candidate.email,
    )

    create_response = client.post(
        "/candidate-profile/",
        json={
            "headline": "Backend Developer",
            "bio": "Aspiring backend developer building FastAPI applications.",
            "phone": "9876543210",
            "location": "Hyderabad",
            "experience_years": 1.5,
            "education": "Bachelor's Degree",
            "skills": [
                "Python",
                "FastAPI",
                "SQL",
            ],
            "linkedin_url": "https://linkedin.com/in/testcandidate",
            "github_url": "https://github.com/testcandidate",
            "portfolio_url": "https://testcandidate.dev",
        },
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert create_response.status_code == 201

    profile = create_response.json()

    assert profile["user_id"] == candidate.id
    assert profile["headline"] == "Backend Developer"
    assert profile["location"] == "Hyderabad"
    assert profile["experience_years"] == "1.5"
    assert profile["skills"] == [
        "Python",
        "FastAPI",
        "SQL",
    ]

    profile_id = profile["id"]

    get_response = client.get(
        "/candidate-profile/me",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert get_response.status_code == 200

    fetched_profile = get_response.json()

    assert fetched_profile["id"] == profile_id
    assert fetched_profile["user_id"] == candidate.id
    assert fetched_profile["headline"] == "Backend Developer"

    update_response = client.put(
        "/candidate-profile/me",
        json={
            "headline": "Python Backend Developer",
            "bio": "Backend developer focused on FastAPI and REST APIs.",
            "phone": "9876543210",
            "location": "Hyderabad",
            "experience_years": 2.0,
            "education": "Bachelor's Degree",
            "skills": [
                "Python",
                "FastAPI",
                "SQL",
                "MySQL",
            ],
            "linkedin_url": "https://linkedin.com/in/testcandidate",
            "github_url": "https://github.com/testcandidate",
            "portfolio_url": "https://testcandidate.dev",
        },
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert update_response.status_code == 200

    updated_profile = update_response.json()

    assert updated_profile["id"] == profile_id
    assert updated_profile["headline"] == "Python Backend Developer"
    assert updated_profile["experience_years"] == "2.0"
    assert updated_profile["skills"] == [
        "Python",
        "FastAPI",
        "SQL",
        "MySQL",
    ]

    duplicate_create_response = client.post(
        "/candidate-profile/",
        json={
            "headline": "Duplicate Profile",
        },
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert duplicate_create_response.status_code == 409

    delete_response = client.delete(
        "/candidate-profile/me",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert delete_response.status_code == 200

    get_deleted_response = client.get(
        "/candidate-profile/me",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert get_deleted_response.status_code == 404


def test_profile_role_restrictions(client, db):
    candidate = create_test_user(
        db,
        "profile_restricted_candidate",
        "profile_restricted_candidate@example.com",
        "Candidate",
    )

    employer = create_test_user(
        db,
        "profile_restricted_employer",
        "profile_restricted_employer@example.com",
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

    employer_create_response = client.post(
        "/candidate-profile/",
        json={
            "headline": "Should Not Be Allowed",
        },
        headers={
            "Authorization": f"Bearer {employer_token}",
        },
    )

    assert employer_create_response.status_code == 403

    employer_get_response = client.get(
        "/candidate-profile/me",
        headers={
            "Authorization": f"Bearer {employer_token}",
        },
    )

    assert employer_get_response.status_code == 403

    candidate_get_response = client.get(
        "/candidate-profile/me",
        headers={
            "Authorization": f"Bearer {candidate_token}",
        },
    )

    assert candidate_get_response.status_code == 404
    