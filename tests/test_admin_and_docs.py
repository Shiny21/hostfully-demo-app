import pytest

from app import create_app
from app.extensions import db


def test_admin_screen_and_openapi_document(client):
    root = client.get("/")
    assert root.status_code == 302
    assert root.headers["Location"].endswith("/admin")
    page = client.get("/admin")
    assert page.status_code == 200
    for form_id in (b"property-form", b"booking-form", b"block-form", b"user-form"):
        assert form_id in page.data
    assert client.get("/docs").status_code == 200
    spec = client.get("/openapi.json").get_json()
    assert spec["openapi"] == "3.1.0"
    for path in (
        "/api/v1/properties",
        "/api/v1/bookings",
        "/api/v1/bookings/{booking_id}/rebook",
        "/api/v1/blocks",
        "/api/v1/admin/users",
    ):
        assert path in spec["paths"]
    assert "BookingCreateSchema" in spec["components"]["schemas"]


def test_demo_role_matrix_and_audit(client, sample_property):
    guest = {"X-Role": "GUEST"}
    manager = {"X-Role": "MANAGER"}
    assert client.get("/api/v1/properties", headers=guest).status_code == 200
    booking = client.post(
        "/api/v1/bookings",
        headers=guest,
        json={
            "property_id": sample_property["id"],
            "guest_name": "Guest",
            "start_date": "2027-02-01",
            "end_date": "2027-02-03",
        },
    )
    assert booking.status_code == 201
    booking_id = booking.get_json()["id"]
    assert client.patch(
        f"/api/v1/bookings/{booking_id}", headers=guest, json={"guest_name": "New Guest"}
    ).status_code == 200
    assert client.post(f"/api/v1/bookings/{booking_id}/cancel", headers=guest).status_code == 200
    assert client.post(f"/api/v1/bookings/{booking_id}/rebook", headers=guest).status_code == 200
    assert client.delete(f"/api/v1/bookings/{booking_id}", headers=guest).status_code == 403
    assert client.post(
        "/api/v1/blocks", headers=guest,
        json={"property_id": sample_property["id"], "start_date": "2027-02-05", "end_date": "2027-02-07"},
    ).status_code == 403
    assert client.post(
        "/api/v1/properties", headers=guest, json={"name": "Denied", "country_code": "PT"}
    ).status_code == 403
    assert client.get("/api/v1/admin/audit", headers=guest).status_code == 403
    assert client.get("/api/v1/admin/users", headers=manager).status_code == 403
    assert client.post(
        "/api/v1/blocks", headers=manager,
        json={"property_id": sample_property["id"], "start_date": "2027-02-05", "end_date": "2027-02-07"},
    ).status_code == 201
    assert client.delete(f"/api/v1/bookings/{booking_id}", headers=manager).status_code == 204
    events = client.get("/api/v1/admin/audit").get_json()
    assert any(event["path"] == "/api/v1/bookings" and event["role"] == "GUEST" for event in events)
    assert all("guest_name" not in event for event in events)


def test_strict_keys_drive_roles_and_user_management():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "API_KEY_REQUIRED": True,
        "API_SECRET_KEY": "test-master-key",
        "AUTO_SEED_DEMO": False,
    })
    with app.app_context():
        client = app.test_client()
        master = {"X-API-Key": "test-master-key"}
        assert client.get("/api/v1/properties").status_code == 401
        assert client.get("/api/v1/properties", headers={"X-API-Key": "wrong"}).status_code == 401
        guest = client.post(
            "/api/v1/admin/users", headers=master, json={"name": "Alice", "role": "GUEST"}
        )
        assert guest.status_code == 201
        guest_id = guest.get_json()["id"]
        guest_key = guest.get_json()["api_key"]
        assert "api_key" not in client.get("/api/v1/admin/users", headers=master).get_json()[0]
        assert client.post(
            "/api/v1/admin/users", headers=master, json={"name": "Alice", "role": "GUEST"}
        ).status_code == 409
        guest_headers = {"X-API-Key": guest_key, "X-Role": "ADMIN"}
        assert client.get("/api/v1/properties", headers=guest_headers).status_code == 200
        assert client.post(
            "/api/v1/properties", headers=guest_headers,
            json={"name": "Forbidden", "country_code": "PT"},
        ).status_code == 403
        assert client.get("/api/v1/admin/audit", headers=guest_headers).status_code == 403
        changed = client.patch(
            f"/api/v1/admin/users/{guest_id}", headers=master,
            json={"name": "Alice Manager", "role": "MANAGER"},
        )
        assert changed.status_code == 200
        assert changed.get_json()["role"] == "MANAGER"
        assert client.post(
            "/api/v1/properties", headers=guest_headers,
            json={"name": "Allowed", "country_code": "PT"},
        ).status_code == 201
        audit = client.get("/api/v1/admin/audit", headers=master).get_json()
        assert any(event["path"] == "/api/v1/admin/users" for event in audit)
        assert client.delete(f"/api/v1/admin/users/{guest_id}", headers=master).status_code == 204
        assert client.get("/api/v1/properties", headers=guest_headers).status_code == 401
        assert client.patch(
            "/api/v1/admin/users/999999", headers=master, json={"role": "GUEST"}
        ).status_code == 404
        db.session.remove()
        db.drop_all()


def test_strict_auth_requires_master_secret():
    with pytest.raises(ValueError, match="API_SECRET_KEY must be set"):
        create_app({"API_KEY_REQUIRED": True, "API_SECRET_KEY": ""})


def test_vercel_requires_persistent_database(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    with pytest.raises(ValueError, match="DATABASE_URL or POSTGRES_URL"):
        create_app()
