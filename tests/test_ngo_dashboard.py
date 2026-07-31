import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, db
from models import User, Donation


def test_ngo_dashboard_renders_for_ngo_user():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with app.test_client() as client:
        with app.app_context():
            user = User.query.filter_by(email="ngo@example.com").first()
            if not user:
                user = User(name="NGO Test", email="ngo@example.com", phone="9999999999", role="ngo", address="Test")
                user.set_password("secret")
                db.session.add(user)
                db.session.commit()

            user_id = user.id

            donation = Donation.query.filter_by(food_name="Test Donation").first()
            if not donation:
                donation = Donation(
                    food_name="Test Donation",
                    food_category="Food",
                    food_type="Vegetables",
                    quantity="10 boxes",
                    servings=10,
                    pickup_address="Test Address",
                    pickup_time=datetime(2025, 1, 1, 0, 0, 0),
                    expiry_time=datetime(2025, 1, 2, 0, 0, 0),
                    donor_id=user_id,
                    status="Available",
                )
                db.session.add(donation)
                db.session.commit()

        with client.session_transaction() as session:
            session["_user_id"] = str(user_id)

        response = client.get("/ngo/dashboard")
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "Verified NGO" in body
        assert "Available Food Donations" in body
        assert "My Accepted Donations" in body


def test_completed_donations_are_visible_on_ngo_dashboard():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with app.test_client() as client:
        with app.app_context():
            user = User.query.filter_by(email="ngo-completed@example.com").first()
            if not user:
                user = User(name="NGO Completed", email="ngo-completed@example.com", phone="9999999998", role="ngo", address="Test")
                user.set_password("secret")
                db.session.add(user)
                db.session.commit()

            user_id = user.id

            completed_donation = Donation.query.filter_by(food_name="Completed Donation").first()
            if not completed_donation:
                completed_donation = Donation(
                    food_name="Completed Donation",
                    food_category="Food",
                    food_type="Vegetables",
                    quantity="5 boxes",
                    servings=5,
                    pickup_address="Completed Address",
                    pickup_time=datetime(2025, 1, 1, 0, 0, 0),
                    expiry_time=datetime(2025, 1, 2, 0, 0, 0),
                    donor_id=user_id,
                    status="Completed",
                    ngo_id=user_id,
                )
                db.session.add(completed_donation)
                db.session.commit()
            else:
                completed_donation.status = "Completed"
                completed_donation.ngo_id = user_id
                db.session.commit()

        with client.session_transaction() as session:
            session["_user_id"] = str(user_id)

        response = client.get("/ngo/dashboard")
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "Completed Donations" in body
        assert "Completed Donation" in body
