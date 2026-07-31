import base64
import hashlib
import secrets
from datetime import datetime, timedelta

from flask import current_app
from flask_mail import Message

from models import db, Notification


def send_email(subject: str, recipient: str, body: str):
    if current_app.config.get("MAIL_SUPPRESS_SEND"):
        return None
    mail = current_app.extensions.get("mail")
    if mail is None:
        return None
    msg = Message(subject=subject, recipients=[recipient], body=body)
    try:
        mail.send(msg)
    except Exception:
        return None
    return msg


def create_notification(user_id: int, title: str, message: str):
    notification = Notification(user_id=user_id, title=title, message=message, is_read=False)
    db.session.add(notification)
    db.session.commit()
    return notification


def generate_password_reset_token(email: str) -> str:
    encoded_email = base64.urlsafe_b64encode(email.encode("utf-8")).decode("utf-8")
    token = secrets.token_urlsafe(24)
    payload = f"{encoded_email}:{token}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{payload}:{digest}"


def verify_password_reset_token(token: str) -> str | None:
    if not token or token.count(":") < 2:
        return None

    payload, digest = token.rsplit(":", 1)
    expected_digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    if not secrets.compare_digest(digest, expected_digest):
        return None

    encoded_email, _ = payload.split(":", 1)
    try:
        return base64.urlsafe_b64decode(encoded_email.encode("utf-8")).decode("utf-8")
    except Exception:
        return None
