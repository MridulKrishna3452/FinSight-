from fastapi.testclient import TestClient


def _register_and_login(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123!", "full_name": "Owner"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_transaction(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "transaction_date": "2026-06-01",
            "merchant_name": "Swiggy",
            "description": "SWIGGY ORDER",
            "amount": "450.00",
            "transaction_type": "expense",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_user_cannot_read_another_users_transaction(client: TestClient) -> None:
    owner_headers = _register_and_login(client, "owner@test.com")
    transaction_id = _create_transaction(client, owner_headers)

    intruder_headers = _register_and_login(client, "intruder@test.com")
    response = client.get(f"/api/v1/transactions/{transaction_id}", headers=intruder_headers)
    assert response.status_code == 404


def test_user_cannot_delete_another_users_transaction(client: TestClient) -> None:
    owner_headers = _register_and_login(client, "owner2@test.com")
    transaction_id = _create_transaction(client, owner_headers)

    intruder_headers = _register_and_login(client, "intruder2@test.com")
    response = client.delete(f"/api/v1/transactions/{transaction_id}", headers=intruder_headers)
    assert response.status_code == 404

    still_there = client.get(f"/api/v1/transactions/{transaction_id}", headers=owner_headers)
    assert still_there.status_code == 200


def test_transaction_list_only_shows_own_transactions(client: TestClient) -> None:
    owner_headers = _register_and_login(client, "owner3@test.com")
    _create_transaction(client, owner_headers)

    other_headers = _register_and_login(client, "other3@test.com")
    response = client.get("/api/v1/transactions", headers=other_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0
