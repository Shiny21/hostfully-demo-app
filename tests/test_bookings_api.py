def test_booking_lifecycle_and_overlap_scenarios(client, sample_property):
    prop_id = sample_property["id"]

    res = client.post(
        "/api/v1/bookings",
        json={
            "property_id": prop_id,
            "guest_name": "Shivani",
            "start_date": "2026-11-11",
            "end_date": "2026-11-16",
        },
    )
    assert res.status_code == 201
    booking = res.get_json()
    booking_id = booking["id"]
    assert booking["status"] == "CONFIRMED"

    conflict_start = client.post(
        "/api/v1/bookings",
        json={
            "property_id": prop_id,
            "guest_name": "Guest B",
            "start_date": "2026-11-09",
            "end_date": "2026-11-11",
        },
    )
    assert conflict_start.status_code == 409
    assert set(conflict_start.get_json()) == {"error", "details"}

    conflict_end = client.post(
        "/api/v1/bookings",
        json={
            "property_id": prop_id,
            "guest_name": "Guest C",
            "start_date": "2026-11-16",
            "end_date": "2026-11-18",
        },
    )
    assert conflict_end.status_code == 409

    cancel_res = client.post(f"/api/v1/bookings/{booking_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.get_json()["status"] == "CANCELED"

    second_res = client.post(
        "/api/v1/bookings",
        json={
            "property_id": prop_id,
            "guest_name": "Replacement Guest",
            "start_date": "2026-11-12",
            "end_date": "2026-11-14",
        },
    )
    assert second_res.status_code == 201
    second_id = second_res.get_json()["id"]

    rebook_conflict = client.post(f"/api/v1/bookings/{booking_id}/rebook")
    assert rebook_conflict.status_code == 409

    del_res = client.delete(f"/api/v1/bookings/{second_id}")
    assert del_res.status_code == 204

    rebook_ok = client.post(f"/api/v1/bookings/{booking_id}/rebook")
    assert rebook_ok.status_code == 200
    assert rebook_ok.get_json()["status"] == "CONFIRMED"
