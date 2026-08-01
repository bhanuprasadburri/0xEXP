import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
DEFAULT_DB_PATH = INSTANCE_DIR / "0xexp.db"


def _build_database_uri() -> str:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        return database_url

    mysql_host = os.getenv("MYSQL_HOST", "127.0.0.1").strip()
    mysql_port = os.getenv("MYSQL_PORT", "3306").strip()
    mysql_database = os.getenv("MYSQL_DATABASE", "0xexp").strip()
    mysql_user = os.getenv("MYSQL_USER", "root").strip()
    mysql_password = os.getenv("MYSQL_PASSWORD", "").strip()

    if mysql_host and mysql_user and mysql_database:
        return f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"

    return "sqlite:///" + str(DEFAULT_DB_PATH)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = _build_database_uri()
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    UPLOAD_FOLDER = str(BASE_DIR / "static" / "uploads")
    INSTANCE_DIR = str(INSTANCE_DIR)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "25"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "false").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@fooddonation.local")
