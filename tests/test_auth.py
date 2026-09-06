


def test_create_user_and_login(client):
    user_data = {
        "username": "testcandidate",
        "email": "testcandidate@example.com",
        "password": "TestPassword123",
        "date_of_birth": "2000-01-01",
    }

    create_response = client.post(
        "/users/",
        json=user_data,
    )

    assert create_response.status_code == 201

    login_response = client.post(
        "/login",
        data={
            "username": "testcandidate@example.com",
            "password": "TestPassword123",
        },
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"