import os
from datetime import date

from flask import Flask, g, jsonify, request
from sqlalchemy import text
from sqlalchemy.pool import NullPool, StaticPool

from app.errors import register_error_handlers
from app.extensions import db
from app.models import AuditEvent, Block, Booking, BookingStatus, Property
from app.routes.admin_api import admin_api_bp
from app.routes.admin_ui import admin_bp
from app.routes.api_docs import docs_bp
from app.routes.blocks import blocks_bp
from app.routes.bookings import bookings_bp
from app.routes.properties import properties_bp


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)

    configured_db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if os.getenv("VERCEL") and not configured_db_url and not (
        test_config and test_config.get("SQLALCHEMY_DATABASE_URI")
    ):
        raise ValueError("DATABASE_URL or POSTGRES_URL is required on Vercel")
    db_url = configured_db_url or "sqlite:///:memory:"
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=db_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        API_KEY_REQUIRED=os.getenv("API_KEY_REQUIRED", "false").lower() == "true",
        API_SECRET_KEY=os.getenv("API_SECRET_KEY", ""),
        AUTO_SEED_DEMO=os.getenv("AUTO_SEED_DEMO", "false").lower() == "true",
    )

    if test_config:
        app.config.update(test_config)

    if app.config["API_KEY_REQUIRED"] and not app.config["API_SECRET_KEY"]:
        raise ValueError("API_SECRET_KEY must be set when API_KEY_REQUIRED=true")

    if app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:":
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
    elif os.getenv("VERCEL") and app.config["SQLALCHEMY_DATABASE_URI"].startswith(
        "postgresql+psycopg2://"
    ):
        # Neon supplies a pooled endpoint; avoid retaining connections across
        # short-lived serverless instances.
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": {"connect_timeout": 10},
            "poolclass": NullPool,
        }

    db.init_app(app)
    register_error_handlers(app)

    app.register_blueprint(properties_bp, url_prefix="/api/v1/properties")
    app.register_blueprint(bookings_bp, url_prefix="/api/v1/bookings")
    app.register_blueprint(blocks_bp, url_prefix="/api/v1/blocks")
    app.register_blueprint(admin_api_bp, url_prefix="/api/v1/admin")
    app.register_blueprint(admin_bp)
    app.register_blueprint(docs_bp)

    @app.after_request
    def record_audit_event(response):
        if (
            request.path.startswith("/api/v1/")
            and request.method in {"POST", "PUT", "PATCH", "DELETE"}
            and response.status_code < 400
        ):
            try:
                db.session.add(
                    AuditEvent(
                        role=getattr(g, "current_role", "ADMIN"),
                        method=request.method,
                        path=request.path,
                        status_code=response.status_code,
                    )
                )
                db.session.commit()
            except Exception:
                db.session.rollback()
                app.logger.exception("Could not record audit event")
        return response

    @app.get("/health")
    def health_check():
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "healthy", "service": "hostfully-booking-api"}), 200

    with app.app_context():
        if db.engine.dialect.name == "postgresql":
            # Concurrent Gunicorn workers or serverless instances may boot together.
            # Keep the schema existence check and creation in one locked transaction.
            with db.engine.begin() as connection:
                connection.execute(text("SELECT pg_advisory_xact_lock(734615927)"))
                db.Model.metadata.create_all(bind=connection)
        else:
            db.create_all()
        if app.config.get("AUTO_SEED_DEMO"):
            seed_demo_data()

    return app


def seed_demo_data() -> None:
    if db.engine.dialect.name == "postgresql":
        db.session.execute(text("SELECT pg_advisory_xact_lock(734615928)"))
    if db.session.query(Property).count() == 0:
        prop = Property(name="Lisbon Oceanfront Villa", country_code="PT")
        db.session.add(prop)
        db.session.flush()
        db.session.add(
            Booking(
                property_id=prop.id,
                guest_name="Alice Wonderland",
                start_date=date(2026, 11, 11),
                end_date=date(2026, 11, 16),
                status=BookingStatus.CONFIRMED,
            )
        )
        db.session.add(
            Block(
                property_id=prop.id,
                start_date=date(2026, 11, 20),
                end_date=date(2026, 11, 22),
            )
        )
    db.session.commit()
