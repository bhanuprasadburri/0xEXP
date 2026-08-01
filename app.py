import os
from pathlib import Path
from datetime import datetime, timezone

import flask_login.login_manager as flask_login_manager_module
from flask import Flask, redirect, url_for, flash
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_mail import Mail
from dotenv import load_dotenv
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from config import Config
from models import db, User, NGO
from routes.public import public_bp
from utils.seed import seed_admin_user, seed_demo_users
from routes.auth import auth_bp
from routes.donor import donor_bp
from routes.ngo import ngo_bp
from routes.admin import admin_bp

load_dotenv()


def _patch_flask_login_datetime() -> None:
    def _utcnow():
        return datetime.now(timezone.utc)

    flask_login_manager_module.datetime = type(
        "CompatDateTime",
        (datetime,),
        {"utcnow": staticmethod(_utcnow)},
    )


_patch_flask_login_datetime()

csrf = CSRFProtect()
mail = Mail()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    flash("Please log in to access this page.", "info")
    return redirect(url_for("auth.login"))


def _ensure_runtime_directories(app: Flask) -> None:
    os.makedirs(app.config.get("INSTANCE_DIR", str(Path(__file__).resolve().parent / "instance")), exist_ok=True)
    os.makedirs(app.config.get("UPLOAD_FOLDER", str(Path(__file__).resolve().parent / "static" / "uploads")), exist_ok=True)


def _initialize_database(app: Flask) -> None:
    with app.app_context():
        try:
            db.engine.connect()
        except Exception as exc:
            app.logger.error("MySQL connection failed: %s", exc)
            raise

        try:
            migration_dir = Path(__file__).resolve().parent / "migrations"
            if migration_dir.exists() and any(migration_dir.glob("versions/*.py")):
                from flask_migrate import upgrade

                upgrade(directory=str(migration_dir))
            else:
                db.create_all()

            inspector = inspect(db.engine)
            if "ngos" in inspector.get_table_names():
                foreign_keys = inspector.get_foreign_keys("ngos")
                has_cascade_fk = any(
                    fk.get("referred_table") == "users"
                    and fk.get("constrained_columns") == ["user_id"]
                    and fk.get("options", {}).get("ondelete") == "CASCADE"
                    for fk in foreign_keys
                )
                if not has_cascade_fk:
                    try:
                        with db.engine.begin() as connection:
                            connection.execute(text("""
                                ALTER TABLE ngos
                                ADD CONSTRAINT ngos_ibfk_1
                                FOREIGN KEY (user_id) REFERENCES users(id)
                                ON DELETE CASCADE
                            """))
                    except Exception as exc:
                        app.logger.warning("Could not add cascade foreign key to ngos: %s", exc)

            seed_admin_user()
            seed_demo_users()
        except Exception as exc:
            app.logger.warning("Database initialization failed; retrying table creation: %s", exc)
            db.create_all()
            seed_admin_user()
            seed_demo_users()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(donor_bp)
    app.register_blueprint(ngo_bp)
    app.register_blueprint(admin_bp)

    from routes.auth import donor_login, ngo_login, donor_register, ngo_register

    csrf.exempt(donor_login)
    csrf.exempt(ngo_login)
    csrf.exempt(donor_register)
    csrf.exempt(ngo_register)

    @app.context_processor
    def inject_user():
        return {"current_user": current_user}

    _ensure_runtime_directories(app)
    _initialize_database(app)

    with app.app_context():
        inspector = inspect(db.engine)
        if "users" in inspector.get_table_names():
            user_columns = {column["name"] for column in inspector.get_columns("users")}
            for column_name, column_type in [
                ("name", "VARCHAR(150)"),
                ("full_name", "VARCHAR(150)"),
                ("city", "VARCHAR(100)"),
                ("state", "VARCHAR(100)"),
                ("created_at", "DATETIME"),
                ("updated_at", "DATETIME"),
            ]:
                if column_name not in user_columns:
                    with db.engine.begin() as connection:
                        if column_name in {"created_at", "updated_at"}:
                            connection.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))
                        else:
                            connection.execute(text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"))

        if "ngos" in inspector.get_table_names():
            ngo_columns = {column["name"] for column in inspector.get_columns("ngos")}
            for column_name, column_type in [
                ("address", "VARCHAR"),
                ("city", "VARCHAR(100)"),
                ("state", "VARCHAR(100)"),
                ("verification_status", "VARCHAR(20)"),
                ("is_verified", "BOOLEAN"),
            ]:
                if column_name not in ngo_columns:
                    with db.engine.begin() as connection:
                        default_value = "'pending'" if column_name in {"verification_status"} else "'false'" if column_name == "is_verified" else "NULL"
                        connection.execute(text(f"ALTER TABLE ngos ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"))
            for ngo in NGO.query.filter((NGO.status.in_([None, "", "pending"])) | (NGO.is_verified.is_(None))).all():
                if ngo.ensure_verified_state():
                    db.session.add(ngo)
            db.session.commit()

        if "donations" in inspector.get_table_names():
            donation_columns = {column["name"] for column in inspector.get_columns("donations")}
            for column_name, column_type in [
                ("category", "VARCHAR(50)"),
                ("food_category", "VARCHAR(50)"),
                ("food_type", "VARCHAR(50)"),
                ("pickup_location", "VARCHAR(255)"),
                ("city", "VARCHAR(100)"),
                ("description", "TEXT"),
                ("additional_notes", "TEXT"),
            ]:
                if column_name not in donation_columns:
                    with db.engine.begin() as connection:
                        connection.execute(text(f"ALTER TABLE donations ADD COLUMN {column_name} {column_type}"))

        if "notifications" in inspector.get_table_names():
            notification_columns = {column["name"] for column in inspector.get_columns("notifications")}
            for column_name, column_type in [
                ("title", "VARCHAR(150)"),
                ("is_read", "BOOLEAN"),
                ("status", "VARCHAR(20)"),
            ]:
                if column_name not in notification_columns:
                    with db.engine.begin() as connection:
                        default_value = "'unread'" if column_name == "status" else "'false'" if column_name == "is_read" else "NULL"
                        connection.execute(text(f"ALTER TABLE notifications ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
