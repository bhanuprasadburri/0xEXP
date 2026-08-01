from datetime import datetime, timezone

from . import db


class Donation(db.Model):
    __tablename__ = "donations"
    __table_args__ = (
        db.Index("ix_donations_donor_status", "donor_id", "status"),
        db.Index("ix_donations_ngo_status", "ngo_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    ngo_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    food_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    food_category = db.Column(db.String(50), nullable=True)
    food_type = db.Column(db.String(50), nullable=True)
    quantity = db.Column(db.String(50), nullable=False)
    servings = db.Column(db.Integer, nullable=False)
    pickup_address = db.Column(db.Text, nullable=False)
    pickup_location = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    pickup_time = db.Column(db.DateTime, nullable=False)
    expiry_time = db.Column(db.DateTime, nullable=False)
    description = db.Column(db.Text, nullable=True)
    additional_notes = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Available")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    donor = db.relationship("User", back_populates="donations", foreign_keys=[donor_id])
    ngo = db.relationship("User", back_populates="accepted_donations", foreign_keys=[ngo_id])
    history = db.relationship("DonationHistory", back_populates="donation", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        if "food_category" in kwargs and "category" not in kwargs:
            kwargs["category"] = kwargs["food_category"]
        if "category" in kwargs and "food_category" not in kwargs:
            kwargs["food_category"] = kwargs["category"]
        if "description" not in kwargs and "additional_notes" in kwargs:
            kwargs["description"] = kwargs["additional_notes"]
        if "additional_notes" not in kwargs and "description" in kwargs:
            kwargs["additional_notes"] = kwargs["description"]
        super().__init__(**kwargs)


class DonationHistory(db.Model):
    __tablename__ = "donation_history"

    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey("donations.id"), nullable=False)
    completed_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    donation = db.relationship("Donation", back_populates="history")
