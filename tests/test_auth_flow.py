import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app, db
from models import User, ContactMessage, Donation
from services.email_service import generate_password_reset_token


def test_public_pages_render():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app.test_client()

    for path in ["/", "/about", "/contact", "/register", "/login"]:
        response = client.get(path)
        assert response.status_code == 200


def test_login_choice_page_renders_with_type_cards():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app.test_client()

    response = client.get("/login-choice")
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    assert "Choose Login Type" in html
    assert "Login as a food donor." in html
    assert "Login as an NGO organization." in html
    assert "/login/donor" in html
    assert "/login/ngo" in html


def test_registration_creates_donor_account():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app.test_client()

    with app.app_context():
        User.query.filter_by(email="newdonor@gmail.com").delete()
        db.session.commit()

    response = client.post(
        "/register",
        data={
            "role": "donor",
            "name": "New Donor",
            "email": "newdonor@gmail.com",
            "phone": "1234567890",
            "address": "123 Test Street",
            "password": "Secret123",
            "confirm_password": "Secret123",
            "organization_name": "Bright Pantry",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        user = User.query.filter_by(email="newdonor@gmail.com").first()
        assert user is not None
        assert user.role == "donor"


def test_donor_registration_route_accepts_post():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app.test_client()

    with app.app_context():
        User.query.filter_by(email="route_donor@gmail.com").delete()
        db.session.commit()

    response = client.post(
        "/register/donor",
        data={
            "name": "Route Donor",
            "email": "route_donor@gmail.com",
            "phone": "1234567890",
            "address": "123 Test Street",
            "password": "Secret123",
            "confirm_password": "Secret123",
            "organization_name": "Bright Pantry",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        user = User.query.filter_by(email="route_donor@gmail.com").first()
        assert user is not None
        assert user.role == "donor"


def test_ngo_registration_auto_verifies_and_redirects_to_dashboard():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app.test_client()

    with app.app_context():
        User.query.filter_by(email="auto_ngo@gmail.com").delete()
        db.session.commit()

    response = client.post(
        "/register/ngo",
        data={
            "name": "Auto Verified NGO",
            "registration_number": "REG-1001",
            "email": "auto_ngo@gmail.com",
            "phone": "1234567890",
            "address": "123 NGO Street",
            "password": "Secret123",
            "confirm_password": "Secret123",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ngo/dashboard")

    with app.app_context():
        user = User.query.filter_by(email="auto_ngo@gmail.com").first()
        assert user is not None
        assert user.role == "ngo"
        assert user.ngo_profile is not None
        assert user.ngo_profile.status == "verified"
        assert user.ngo_profile.is_verified is True


def test_login_redirects_to_dashboard_for_ngo():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(email="ngo@gmail.com").first()
        if not user:
            user = User(name="NGO Test", email="ngo@gmail.com", phone="9999999999", role="ngo", address="Test")
            user.set_password("secret")
            db.session.add(user)
            db.session.commit()

    response = client.post(
        "/login",
        data={"email": "ngo@gmail.com", "password": "Secret123"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/ngo/dashboard")


def test_login_accepts_case_insensitive_email_lookup():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(email="MixedCaseUser@gmail.com").first()
        if not user:
            user = User(name="Mixed Case User", email="MixedCaseUser@gmail.com", phone="1112223333", role="donor", address="Test")
            user.set_password("Secret123")
            db.session.add(user)
            db.session.commit()

    response = client.post(
        "/login",
        data={"role": "donor", "email": "mixedcaseuser@gmail.com", "password": "Secret123"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/donor/dashboard")


def test_donor_login_allows_valid_credentials_without_csrf_token():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=True, SECRET_KEY="test-secret")
    client = app.test_client()

    with app.app_context():
        email = "csrf_test@gmail.com"
        User.query.filter_by(email=email).delete()
        db.session.commit()
        user = User(full_name="CSRF Test", email=email, phone="1112223333", role="donor", address="Test")
        user.set_password("Secret123")
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/login/donor",
        data={"email": email, "password": "Secret123"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/donor/dashboard")


def test_donor_and_ngo_login_accept_non_gmail_email_addresses():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app.test_client()

    with app.app_context():
        donor = User.query.filter_by(email="donor.non.gmail@example.net").first()
        if not donor:
            donor = User(full_name="Non Gmail Donor", email="donor.non.gmail@example.net", phone="1112223333", role="donor", address="Test")
            donor.set_password("Secret123")
            db.session.add(donor)

        ngo = User.query.filter_by(email="ngo.non.gmail@example.net").first()
        if not ngo:
            ngo = User(full_name="Non Gmail NGO", email="ngo.non.gmail@example.net", phone="4445556666", role="ngo", address="Test")
            ngo.set_password("Secret123")
            db.session.add(ngo)

        db.session.commit()

    donor_response = client.post(
        "/login/donor",
        data={"email": "donor.non.gmail@example.net", "password": "Secret123"},
        follow_redirects=False,
    )
    assert donor_response.status_code == 302
    assert donor_response.headers["Location"].endswith("/donor/dashboard")

    ngo_response = client.post(
        "/login/ngo",
        data={"email": "ngo.non.gmail@example.net", "password": "Secret123"},
        follow_redirects=False,
    )
    assert ngo_response.status_code == 302
    assert ngo_response.headers["Location"].endswith("/ngo/dashboard")


def test_password_reset_request_redirects_to_login():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app.test_client()

    response = client.post(
        "/forgot-password",
        data={"email": "premium_donor@gmail.com"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_password_reset_token_updates_password():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(email="reset_user@gmail.com").first()
        if not user:
            user = User(full_name="Reset User", email="reset_user@gmail.com", phone="9999999999", role="donor", address="Test")
            user.set_password("oldsecret")
            db.session.add(user)
            db.session.commit()

        token = generate_password_reset_token(user.email)

    response = client.post(
        f"/reset-password/{token}",
        data={"password": "NewSecret123", "confirm_password": "NewSecret123"},
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        user = User.query.filter_by(email="reset_user@gmail.com").first()
        assert user is not None
        assert user.check_password("NewSecret123")


def test_contact_form_persists_to_database():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app.test_client()

    response = client.post(
        "/contact",
        data={
            "name": "Integration User",
            "email": "integration@gmail.com",
            "subject": "Test subject",
            "message": "Hello from the test",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        message = ContactMessage.query.filter_by(email="integration@gmail.com").first()
        assert message is not None
        assert message.subject == "Test subject"


def test_donation_form_persists_to_database():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(email="donation_user@gmail.com").first()
        if not user:
            user = User(full_name="Donation User", email="donation_user@gmail.com", phone="2233445566", role="donor", address="Test")
            user.set_password("secret")
            db.session.add(user)
            db.session.commit()
        user_id = user.id

    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True

    response = client.post(
        "/donor/add-donation",
        data={
            "food_name": "Rice Pack",
            "food_category": "Cooked",
            "food_type": "Vegetarian",
            "quantity": "10 boxes",
            "servings": "20",
            "pickup_address": "123 Test Street",
            "pickup_location": "Test Plaza",
            "pickup_time": "2030-01-01T12:00",
            "expiry_time": "2030-01-02T12:00",
            "additional_notes": "Freshly cooked",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    with app.app_context():
        donation = Donation.query.filter_by(donor_id=user_id).order_by(Donation.id.desc()).first()
        assert donation is not None
        assert donation.food_name == "Rice Pack"


def test_donor_dashboard_renders_premium_workspace():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(email="premium_donor@example.com").first()
        if not user:
            user = User(name="Premium Donor", email="premium_donor@example.com", phone="5555555555", role="donor", address="Test")
            user.set_password("secret")
            db.session.add(user)
            db.session.commit()
        user_id = user.id

    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True

    response = client.get("/donor/dashboard")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Welcome back" in body or "Donor Workspace" in body
