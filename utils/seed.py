from models import db, User


def seed_admin_user():
    admin = User.query.filter_by(email="admin@fooddonation.local").first()
    if admin:
        admin.name = "System Administrator"
        admin.full_name = "System Administrator"
        admin.role = "admin"
        admin.set_password("Admin@123")
        db.session.add(admin)
        db.session.commit()
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


def seed_demo_users():
    demo_accounts = [
        ("admin@fooddonation.local", "admin", "Admin@123"),
        ("ngo@gmail.com", "ngo", "Secret123"),
        ("donor@gmail.com", "donor", "Secret123"),
    ]

    for email, role, password in demo_accounts:
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(name=email.split("@", 1)[0].title(), email=email, phone="9999999999", role=role, address="Demo")
            db.session.add(user)
        user.full_name = user.full_name or user.name or email.split("@", 1)[0].title()
        user.name = user.full_name
        user.role = role
        user.set_password(password)
        db.session.add(user)

    db.session.commit()
