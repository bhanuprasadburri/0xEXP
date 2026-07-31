from models import db, User, NGO
from werkzeug.security import generate_password_hash


def seed_admin_user():
    admin = User.query.filter_by(email="admin@fooddonation.local").first()
    if admin:
        return
    admin_user = User(
        name="System Administrator",
        email="admin@fooddonation.local",
        phone="9999999999",
        address="Head Office",
        role="admin",
    )
    admin_user.set_password("Admin@123")
    db.session.add(admin_user)
    db.session.commit()
