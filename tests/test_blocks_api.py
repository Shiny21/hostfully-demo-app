def test_block_crud_and_booking_conflict(client, sample_property):
    prop_id = sample_property["id"]

    b_res = client.post(
        "/api/v1/blocks",
        json={"property_id": prop_id, "start_date": "2026-11-20", "end_date": "2026-11-25"},
    )
    assert b_res.status_code == 201
    block_id = b_res.get_json()["id"]

    bk_conflict = client.post(
        "/api/v1/bookings",
        json={
            "property_id": prop_id,
            "guest_name": "Blocked Guest",
            "start_date": "2026-11-25",
            "end_date": "2026-11-27",
        },
    )
    assert bk_conflict.status_code == 409

    upd_res = client.patch(
        f"/api/v1/blocks/{block_id}",
        json={"end_date": "2026-11-23"},
    )
    assert upd_res.status_code == 200

    bk_ok = client.post(
        "/api/v1/bookings",
        json={
            "property_id": prop_id,
            "guest_name": "Allowed Guest",
            "start_date": "2026-11-25",
            "end_date": "2026-11-27",
        },
    )
    assert bk_ok.status_code == 201

    del_res = client.delete(f"/api/v1/blocks/{block_id}")
    assert del_res.status_code == 204
