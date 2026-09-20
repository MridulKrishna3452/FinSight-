from fastapi.testclient import TestClient

from app.core.security import hash_password, verify_password


def test_password_hashing_roundtrip() -> None:
    hashed = hash_password("SuperSecret123!")
    assert hashed != "SuperSecret123!"
    assert verify_password("SuperSecret123!", hashed)
    assert not verify_password("WrongPassword", hashed)


def test_register_creates_user_and_returns_tokens(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "new_user@test.com", "password": "StrongPass123!", "full_name": "New User"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "new_user@test.com"
    assert "access_token" in body
    assert "finsight_refresh_token" in response.cookies


def test_register_duplicate_email_fails(client: TestClient) -> None:
    payload = {"email": "dup@test.com", "password": "StrongPass123!", "full_name": "Dup User"}
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


def test_login_with_wrong_password_fails(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login_test@test.com",
            "password": "CorrectPass123!",
            "full_name": "Login Test",
        },
    )
    response = client.post(
        "/api/v1/auth/login", json={"email": "login_test@test.com", "password": "WrongPass"}
    )
    assert response.status_code == 401


def test_login_success_returns_access_token(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"email": "login_ok@test.com", "password": "CorrectPass123!", "full_name": "Login OK"},
    )
    response = client.post(
        "/api/v1/auth/login", json={"email": "login_ok@test.com", "password": "CorrectPass123!"}
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_protected_route_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_protected_route_with_valid_token(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert "email" in response.json()


def test_refresh_flow_rotates_token(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh_test@test.com",
            "password": "CorrectPass123!",
            "full_name": "Refresh Test",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login", json={"email": "refresh_test@test.com", "password": "CorrectPass123!"}
    )
    assert "finsight_refresh_token" in login_response.cookies

    refresh_response = client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 200
    assert refresh_response.json()["access_token"]


def test_logout_revokes_refresh_token(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "logout_test@test.com",
            "password": "CorrectPass123!",
            "full_name": "Logout Test",
        },
    )
    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200
