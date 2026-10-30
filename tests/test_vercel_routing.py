from app.vercel_routing import OriginalPathMiddleware


def test_vercel_rewrite_preserves_flask_routes(client, app):
    app.wsgi_app = OriginalPathMiddleware(app.wsgi_app)

    root = client.get("/api/index?__vercel_path=")
    assert root.status_code == 302
    assert root.headers["Location"].endswith("/admin")
    assert client.get("/api/index?__vercel_path=admin").status_code == 200
    assert client.get("/api/index?__vercel_path=docs").status_code == 200
    assert client.get("/api/index?__vercel_path=health").get_json()["status"] == "healthy"

    response = client.get("/api/index?__vercel_path=api/v1/bookings&status=CONFIRMED")
    assert response.status_code == 200
    assert response.get_json() == []
