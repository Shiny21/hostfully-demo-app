import pytest

from app import create_app
from app.extensions import db


@pytest.fixture()
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "API_KEY_REQUIRED": False,
            "AUTO_SEED_DEMO": False,
        }
    )
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def sample_property(client):
    resp = client.post(
        "/api/v1/properties",
        json={"name": "Oceanview Penthouse", "country_code": "pt"},
    )
    assert resp.status_code == 201
    return resp.get_json()
