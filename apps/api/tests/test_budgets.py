from datetime import date

from fastapi.testclient import TestClient

from app.services.budget_service import status_for_percent


def test_status_thresholds() -> None:
    assert status_for_percent(10) == "green"
    assert status_for_percent(69.9) == "green"
    assert status_for_percent(70) == "yellow"
    assert status_for_percent(89.9) == "yellow"
    assert status_for_percent(90) == "red"
    assert status_for_percent(150) == "red"


def _create_expense(
    client: TestClient, headers: dict[str, str], amount: str, txn_date: str
) -> None:
    response = client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "transaction_date": txn_date,
            "merchant_name": "BigBasket",
            "description": "GROCERY SHOPPING",
            "amount": amount,
            "transaction_type": "expense",
            "category": "Groceries",
        },
    )
    assert response.status_code == 201


def test_budget_progress_calculation(client: TestClient, auth_headers: dict[str, str]) -> None:
    today = date.today()
    create_response = client.post(
        "/api/v1/budgets",
        headers=auth_headers,
        json={
            "name": "Groceries Budget",
            "category": "Groceries",
            "monthly_limit": "1000.00",
            "month": today.month,
            "year": today.year,
        },
    )
    assert create_response.status_code == 201
    budget = create_response.json()
    assert budget["spent"] == "0.00" or float(budget["spent"]) == 0.0

    _create_expense(client, auth_headers, "500.00", today.isoformat())

    list_response = client.get("/api/v1/budgets", headers=auth_headers)
    assert list_response.status_code == 200
    updated = next(b for b in list_response.json() if b["id"] == budget["id"])
    assert float(updated["spent"]) == 500.0
    assert updated["percent_consumed"] == 50.0
    assert updated["status"] == "green"


def test_budget_status_turns_red_over_90_percent(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    today = date.today()
    create_response = client.post(
        "/api/v1/budgets",
        headers=auth_headers,
        json={
            "name": "Tight Budget",
            "category": "Groceries",
            "monthly_limit": "1000.00",
            "month": today.month,
            "year": today.year,
        },
    )
    budget_id = create_response.json()["id"]

    _create_expense(client, auth_headers, "950.00", today.isoformat())

    list_response = client.get("/api/v1/budgets", headers=auth_headers)
    updated = next(b for b in list_response.json() if b["id"] == budget_id)
    assert updated["status"] == "red"


def test_duplicate_budget_same_category_month_rejected(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    today = date.today()
    payload = {
        "name": "Dining Budget",
        "category": "Dining",
        "monthly_limit": "2000.00",
        "month": today.month,
        "year": today.year,
    }
    first = client.post("/api/v1/budgets", headers=auth_headers, json=payload)
    assert first.status_code == 201
    second = client.post("/api/v1/budgets", headers=auth_headers, json=payload)
    assert second.status_code == 409
