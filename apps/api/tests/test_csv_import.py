import io

from fastapi.testclient import TestClient

from app.services import csv_import_service

SAMPLE_CSV = (
    "date,description,amount,type,merchant,payment_method\n"
    "2026-01-03,SWIGGY ORDER,-450,expense,Swiggy,UPI\n"
    "2026-01-05,SALARY CREDIT,75000,income,Acme Corp,Bank Transfer\n"
    "2026-01-06,UBER TRIP,-220,expense,Uber,UPI\n"
)


def test_detect_columns_handles_standard_headers() -> None:
    column_map = csv_import_service.detect_columns(
        ["date", "description", "amount", "type", "merchant", "payment_method"]
    )
    assert column_map["date"] == "date"
    assert column_map["amount"] == "amount"


def test_detect_columns_handles_alternative_headers() -> None:
    column_map = csv_import_service.detect_columns(
        ["txn_date", "narration", "value", "dr_cr", "payee", "mode"]
    )
    assert column_map["date"] == "txn_date"
    assert column_map["description"] == "narration"
    assert column_map["amount"] == "value"


def test_build_preview_returns_rows_and_flags_valid() -> None:
    preview_rows, column_map, total = csv_import_service.build_preview(SAMPLE_CSV.encode())
    assert total == 3
    assert len(preview_rows) == 3
    assert all(row.valid for row in preview_rows)


def test_build_preview_raises_on_missing_required_columns() -> None:
    bad_csv = b"foo,bar\n1,2\n"
    try:
        csv_import_service.build_preview(bad_csv)
        raise AssertionError("Expected CSVValidationError")
    except csv_import_service.CSVValidationError:
        pass


def test_preview_endpoint(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/imports/csv/preview",
        headers=auth_headers,
        files={"file": ("sample.csv", io.BytesIO(SAMPLE_CSV.encode()), "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 3
    assert len(body["preview_rows"]) == 3


def test_full_import_flow_creates_transactions(
    client: TestClient, auth_headers: dict[str, str], monkeypatch, db_session
) -> None:
    from app.api.v1 import imports as imports_module

    def _run_synchronously(job_id: str, content_b64: str) -> None:
        imports_module.process_csv_import_task.run(job_id, content_b64)
        # The task uses its own DB session; expire this test's session so the
        # next query reflects the task's committed changes instead of stale cache.
        db_session.commit()

    monkeypatch.setattr(imports_module.process_csv_import_task, "delay", _run_synchronously)

    upload_response = client.post(
        "/api/v1/imports/csv",
        headers=auth_headers,
        files={"file": ("sample.csv", io.BytesIO(SAMPLE_CSV.encode()), "text/csv")},
    )
    assert upload_response.status_code == 202
    job_id = upload_response.json()["id"]

    status_response = client.get(f"/api/v1/imports/{job_id}", headers=auth_headers)
    assert status_response.status_code == 200
    job = status_response.json()
    assert job["status"] == "completed"
    assert job["imported_rows"] == 3

    list_response = client.get("/api/v1/transactions", headers=auth_headers)
    assert list_response.json()["total"] == 3


def test_import_rejects_non_csv_file(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/imports/csv",
        headers=auth_headers,
        files={"file": ("sample.txt", io.BytesIO(b"not a csv"), "text/plain")},
    )
    assert response.status_code == 400
