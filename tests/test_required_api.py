import pytest


def booking_payload(property_id, start="2026-12-10", end="2026-12-15"):
    return {
        "property_id": property_id,
        "guest_name": "Review Guest",
        "start_date": start,
        "end_date": end,
    }


def block_payload(property_id, start="2026-12-20", end="2026-12-25"):
    return {"property_id": property_id, "start_date": start, "end_date": end}


def assert_error(response, status):
    assert response.status_code == status
    assert set(response.get_json()) == {"error", "details"}
    assert response.get_json()["details"]


def test_property_create_read_list_and_missing(client):
    response = client.post(
        "/api/v1/properties", json={"name": "  Test Villa  ", "country_code": "pt"}
    )
    assert response.status_code == 201
    prop = response.get_json()
    assert prop["name"] == "Test Villa"
    assert prop["country_code"] == "PT"
    assert client.get(f"/api/v1/properties/{prop['id']}").get_json() == prop
    assert prop in client.get("/api/v1/properties").get_json()
    assert_error(client.get("/api/v1/properties/999999"), 404)
    assert_error(client.post("/api/v1/properties", json={"name": "Villa"}), 400)
    assert_error(client.post("/api/v1/properties", json={"name": "Villa", "country_code": "123"}), 400)
    assert_error(client.post("/api/v1/properties", json={"name": "Villa", "country_code": "ÅB"}), 400)


def test_booking_read_list_update_cancel_rebook_delete(client, sample_property):
    prop_id = sample_property["id"]
    created = client.post("/api/v1/bookings", json=booking_payload(prop_id))
    assert created.status_code == 201
    booking_id = created.get_json()["id"]
    assert client.get(f"/api/v1/bookings/{booking_id}").get_json() == created.get_json()
    assert len(client.get(f"/api/v1/bookings?property_id={prop_id}&status=CONFIRMED").get_json()) == 1
    assert client.get("/api/v1/bookings?status=CANCELED").get_json() == []

    updated = client.put(
        f"/api/v1/bookings/{booking_id}",
        json={"guest_name": "Updated Guest", "start_date": "2026-12-11", "end_date": "2026-12-16"},
    )
    assert updated.status_code == 200
    assert updated.get_json()["guest_name"] == "Updated Guest"
    assert updated.get_json()["start_date"] == "2026-12-11"
    assert_error(client.post(f"/api/v1/bookings/{booking_id}/rebook"), 409)
    assert client.post(f"/api/v1/bookings/{booking_id}/cancel").get_json()["status"] == "CANCELED"
    assert len(client.get("/api/v1/bookings?status=CANCELED").get_json()) == 1
    assert client.post(f"/api/v1/bookings/{booking_id}/rebook").get_json()["status"] == "CONFIRMED"
    assert client.delete(f"/api/v1/bookings/{booking_id}").status_code == 204
    assert_error(client.get(f"/api/v1/bookings/{booking_id}"), 404)


def test_booking_update_checks_other_bookings_and_blocks(client, sample_property):
    prop_id = sample_property["id"]
    first = client.post("/api/v1/bookings", json=booking_payload(prop_id))
    assert first.status_code == 201
    second = client.post(
        "/api/v1/bookings", json=booking_payload(prop_id, "2026-12-17", "2026-12-19")
    )
    assert second.status_code == 201
    second_id = second.get_json()["id"]
    assert_error(
        client.patch(f"/api/v1/bookings/{second_id}", json={"start_date": "2026-12-15"}),
        409,
    )
    block = client.post("/api/v1/blocks", json=block_payload(prop_id))
    assert block.status_code == 201
    assert_error(
        client.patch(f"/api/v1/bookings/{second_id}", json={"end_date": "2026-12-20"}),
        409,
    )
    assert client.get(f"/api/v1/bookings/{second_id}").get_json()["end_date"] == "2026-12-19"


def test_block_read_list_update_delete_and_conflicts(client, sample_property):
    prop_id = sample_property["id"]
    created = client.post("/api/v1/blocks", json=block_payload(prop_id))
    assert created.status_code == 201
    block_id = created.get_json()["id"]
    assert client.get(f"/api/v1/blocks/{block_id}").get_json() == created.get_json()
    assert len(client.get(f"/api/v1/blocks?property_id={prop_id}").get_json()) == 1
    assert_error(
        client.post("/api/v1/blocks", json=block_payload(prop_id, "2026-12-25", "2026-12-27")),
        409,
    )
    booking = client.post(
        "/api/v1/bookings", json=booking_payload(prop_id, "2026-12-28", "2026-12-30")
    )
    assert booking.status_code == 201
    assert_error(client.patch(f"/api/v1/blocks/{block_id}", json={"end_date": "2026-12-28"}), 409)
    updated = client.put(f"/api/v1/blocks/{block_id}", json={"end_date": "2026-12-26"})
    assert updated.status_code == 200
    assert updated.get_json()["end_date"] == "2026-12-26"
    assert client.delete(f"/api/v1/blocks/{block_id}").status_code == 204
    assert_error(client.get(f"/api/v1/blocks/{block_id}"), 404)


@pytest.mark.parametrize(
    "path,payload",
    [
        ("/api/v1/properties", {"name": ""}),
        ("/api/v1/bookings", {}),
        ("/api/v1/bookings", {"property_id": 1, "guest_name": "A", "start_date": "bad", "end_date": "2026-12-15"}),
        ("/api/v1/bookings", {"property_id": 1, "guest_name": "A", "start_date": "2026-12-15", "end_date": "2026-12-15"}),
        ("/api/v1/blocks", {"property_id": 1, "start_date": "2026-12-20", "end_date": "2026-12-19"}),
    ],
)
def test_invalid_create_payloads_return_structured_400(client, path, payload):
    assert_error(client.post(path, json=payload), 400)


def test_missing_references_and_invalid_updates(client, sample_property):
    prop_id = sample_property["id"]
    assert_error(client.post("/api/v1/bookings", json=booking_payload(999999)), 404)
    assert_error(client.post("/api/v1/blocks", json=block_payload(999999)), 404)
    assert_error(client.get("/api/v1/bookings/999999"), 404)
    assert_error(client.get("/api/v1/blocks/999999"), 404)
    assert_error(client.delete("/api/v1/bookings/999999"), 404)
    assert_error(client.delete("/api/v1/blocks/999999"), 404)
    assert_error(client.get("/api/v1/bookings?status=UNKNOWN"), 400)
    assert_error(client.get("/api/v1/blocks?property_id=abc"), 400)
    assert_error(client.post("/api/v1/properties", data="{", content_type="application/json"), 400)

    booking = client.post("/api/v1/bookings", json=booking_payload(prop_id)).get_json()
    block = client.post("/api/v1/blocks", json=block_payload(prop_id)).get_json()
    assert_error(client.patch(f"/api/v1/bookings/{booking['id']}", json={}), 400)
    assert_error(client.patch(f"/api/v1/blocks/{block['id']}", json={}), 400)
    assert_error(
        client.patch(f"/api/v1/bookings/{booking['id']}", json={"end_date": "2026-12-10"}),
        400,
    )
    assert_error(client.patch(f"/api/v1/blocks/{block['id']}", json={"end_date": "2026-12-20"}), 400)


def test_canceled_booking_does_not_prevent_block(client, sample_property):
    prop_id = sample_property["id"]
    booking = client.post("/api/v1/bookings", json=booking_payload(prop_id)).get_json()
    client.post(f"/api/v1/bookings/{booking['id']}/cancel")
    block = client.post(
        "/api/v1/blocks", json=block_payload(prop_id, "2026-12-10", "2026-12-15")
    )
    assert block.status_code == 201
    assert_error(client.post(f"/api/v1/bookings/{booking['id']}/rebook"), 409)
