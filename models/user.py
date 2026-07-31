from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from . import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(150), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="donor")
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    organization_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    donations = db.relationship("Donation", back_populates="donor", foreign_keys="Donation.donor_id", cascade="all, delete-orphan")
    accepted_donations = db.relationship("Donation", back_populates="ngo", foreign_keys="Donation.ngo_id", cascade="all, delete-orphan")
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    ngo_profile = db.relationship("NGO", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __init__(self, full_name=None, name=None, **kwargs):
        super().__init__(**kwargs)
        resolved_name = full_name or name or kwargs.get("full_name") or kwargs.get("name") or ""
        self.full_name = resolved_name
        self.name = resolved_name or kwargs.get("email", "")
        if not self.full_name:
            self.full_name = kwargs.get("email", "")
            self.name = self.full_name

    @property
    def display_name(self):
        return self.full_name or self.name or ""

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class NGO(db.Model):
    __tablename__ = "ngos"

    id = db.Column(db.Integer, primary_key=True)
    organization_name = db.Column(db.String(255), nullable=False)
    registration_number = db.Column(db.String(100), nullable=False, unique=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    verification_status = db.Column(db.String(20), nullable=False, default="pending")
    status = db.Column(db.String(20), nullable=False, default="pending")
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    user = db.relationship("User", back_populates="ngo_profile")

    def ensure_verified_state(self):
        changed = False
        if self.status in (None, "", "pending"):
            self.status = "verified"
            changed = True
        if self.is_verified is None:
            self.is_verified = True
            changed = True
        if not self.is_verified and self.status != "rejected":
            self.is_verified = True
            self.status = "verified"
            changed = True
        return changed
