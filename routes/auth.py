import re
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from sqlalchemy import func
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

from models import db, User, NGO, Notification
from services.email_service import send_email, generate_password_reset_token, verify_password_reset_token
from utils.email_validation import get_gmail_validation_message, is_gmail_address

auth_bp = Blueprint("auth", __name__)


def _normalize_email(email):
    return (email or "").strip().lower()


def _find_user_by_email(email, role=None):
    normalized_email = _normalize_email(email)
    query = User.query.filter(func.lower(User.email) == normalized_email)
    if role:
        query = query.filter(User.role == role)
    return query.first()


def _authenticate_user(email, password, role=None):
    if not email or not password:
        return None

    user = _find_user_by_email(email, role=role)
    if user and user.check_password(password):
        return user
    return None


def _validate_password(password, confirm_password=None):
    if not password:
        return "Password is required."
    if confirm_password is not None and password != confirm_password:
        return "Passwords do not match."
    if not re.search(r"[A-Z]", password) or not re.search(r"[0-9]", password) or len(password) < 8:
        return "Password must be at least 8 characters and include a number and uppercase letter."
    return None


def _create_user_account(role, form_data, *, redirect_endpoint, error_endpoint):
    name = (form_data.get("name") or "").strip()
    email = _normalize_email(form_data.get("email", ""))
    phone = (form_data.get("phone") or "").strip()
    address = (form_data.get("address") or "").strip()
    password = form_data.get("password", "")
    confirm_password = form_data.get("confirm_password", "")
    organization_name = (form_data.get("organization_name") or "").strip()
    registration_number = (form_data.get("registration_number") or "").strip()

    if not all([name, email, phone, address, password]):
        flash("Please fill in all required fields.", "danger")
        return redirect(url_for(error_endpoint))

    if not is_gmail_address(email):
        flash(get_gmail_validation_message(), "danger")
        return redirect(url_for(error_endpoint))

    password_error = _validate_password(password, confirm_password)
    if password_error:
        flash(password_error, "danger")
        return redirect(url_for(error_endpoint))

    if _find_user_by_email(email):
        flash("An account with this email already exists.", "danger")
        return redirect(url_for(error_endpoint))

    user = User(
        full_name=name,
        email=email,
        phone=phone,
        address=address,
        role=role,
        organization_name=organization_name or name,
    )
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.flush()

        if role == "ngo":
            existing_ngo = NGO.query.filter_by(user_id=user.id).first()
            if existing_ngo:
                db.session.delete(existing_ngo)

            base_registration_number = registration_number or "REG-DEFAULT"
            unique_registration_number = base_registration_number
            suffix = 1
            while NGO.query.filter_by(registration_number=unique_registration_number).first():
                unique_registration_number = f"{base_registration_number}-{suffix}"
                suffix += 1

            ngo = NGO(
                organization_name=organization_name or name,
                registration_number=unique_registration_number,
                address=address,
                status="verified",
                verification_status="verified",
                is_verified=True,
                user_id=user.id,
            )
            db.session.add(ngo)

        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("We could not create your account right now. Please try again.", "danger")
        return redirect(url_for(error_endpoint))

    if role == "ngo":
        flash("Registration successful! Please log in to continue.", "success")
        return redirect(url_for("auth.ngo_login"))

    flash("Registration successful! Please log in to continue.", "success")
    return redirect(url_for("auth.donor_login"))


def _register_user(role, form_data):
    return _create_user_account(
        role,
        form_data,
        redirect_endpoint="auth.donor_login" if role == "donor" else "auth.ngo_login",
        error_endpoint="auth.register",
    )


class DonorRegistrationForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=150)])
    organization_name = StringField("Organization Name", validators=[DataRequired(), Length(min=2, max=255)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Mobile Number", validators=[DataRequired(), Length(min=8, max=20)])
    address = StringField("Address", validators=[DataRequired(), Length(min=5, max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=100)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Register")

    def validate_email(self, field):
        if not is_gmail_address(field.data):
            raise ValidationError(get_gmail_validation_message())
        if _find_user_by_email(field.data):
            raise ValidationError("Email already exists.")


class NGORegistrationForm(FlaskForm):
    name = StringField("NGO Name", validators=[DataRequired(), Length(min=2, max=150)])
    registration_number = StringField("Registration Number", validators=[DataRequired(), Length(min=3, max=100)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Mobile", validators=[DataRequired(), Length(min=8, max=20)])
    address = StringField("Address", validators=[DataRequired(), Length(min=5, max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=100)])
    submit = SubmitField("Register")

    def validate_email(self, field):
        if not is_gmail_address(field.data):
            raise ValidationError(get_gmail_validation_message())
        if _find_user_by_email(field.data):
            raise ValidationError("Email already exists.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

    def validate_email(self, field):
        if not is_gmail_address(field.data):
            raise ValidationError(get_gmail_validation_message())



@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        role = request.form.get("role", "donor")
        return _register_user(role, request.form)

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        role = (request.form.get("role") or "").strip().lower()
        email = _normalize_email(request.form.get("email", ""))
        password = request.form.get("password", "")

        if not is_gmail_address(email):
            flash(get_gmail_validation_message(), "danger")
            return redirect(url_for("auth.login"))

        remember = (request.form.get("remember") or "").lower() in {"1", "true", "yes", "y", "on"}

        if role == "donor":
            user = _authenticate_user(email, password, role="donor")
            if user:
                login_user(user, remember=remember)
                flash("Welcome back!", "success")
                return redirect(url_for("donor.dashboard"))
            flash("Invalid donor credentials.", "danger")
            return redirect(url_for("auth.login"))

        if role == "ngo":
            user = _authenticate_user(email, password, role="ngo")
            if user:
                login_user(user, remember=remember)
                flash("Welcome back!", "success")
                return redirect(url_for("ngo.dashboard"))
            flash("Invalid NGO credentials.", "danger")
            return redirect(url_for("auth.login"))

        if role == "admin":
            user = _authenticate_user(email, password, role="admin")
            if user:
                login_user(user, remember=remember)
                flash("Welcome back!", "success")
                return redirect(url_for("admin.dashboard"))
            flash("Invalid admin credentials.", "danger")
            return redirect(url_for("auth.login"))

        registration_number = request.form.get("registration_number", "").strip()
        if registration_number:
            ngo = NGO.query.filter_by(registration_number=registration_number).first()
            if ngo:
                user = db.session.get(User, ngo.user_id)
                if user and _normalize_email(user.email) == email and user.check_password(password):
                    login_user(user, remember=remember)
                    flash("Welcome back!", "success")
                    return redirect(url_for("ngo.dashboard"))

        user = _authenticate_user(email, password)
        if user:
            login_user(user, remember=remember)
            flash("Welcome back!", "success")
            return redirect(url_for("ngo.dashboard") if user.role == "ngo" else url_for("donor.dashboard"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("auth.login"))

    return render_template("auth/login_choice.html")


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        address = (request.form.get("address") or "").strip()
        city = (request.form.get("city") or "").strip()
        state = (request.form.get("state") or "").strip()
        organization_name = (request.form.get("organization_name") or "").strip()

        if not full_name:
            flash("Full name is required.", "danger")
            return redirect(url_for("auth.profile"))

        try:
            current_user.full_name = full_name
            current_user.name = full_name
            current_user.phone = phone or current_user.phone
            current_user.address = address or current_user.address
            current_user.city = city or current_user.city
            current_user.state = state or current_user.state
            if current_user.role == "ngo" and organization_name:
                current_user.organization_name = organization_name
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("We could not update your profile right now.", "danger")
            return redirect(url_for("auth.profile"))

        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    completed_count = 0
    donation_count = 0
    completion_rate = 0
    if current_user.role == "donor":
        donation_count = current_user.donations.count() if hasattr(current_user.donations, 'count') else len(current_user.donations)
        completed_count = sum(1 for donation in current_user.donations if donation.status == "Completed")
        completion_rate = round((completed_count / donation_count * 100), 1) if donation_count else 0

    return render_template(
        "auth/profile.html",
        donations=[d for d in current_user.donations] if current_user.role == "donor" else [],
        completion_rate=completion_rate,
    )


@auth_bp.route("/notifications")
@login_required
def notifications():
    user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template("auth/notifications.html", notifications=user_notifications)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("public.home"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = _normalize_email(request.form.get("email", ""))
        if not is_gmail_address(email):
            flash(get_gmail_validation_message(), "danger")
            return redirect(url_for("auth.forgot_password"))
        user = _find_user_by_email(email)
        if user:
            token = generate_password_reset_token(email)
            reset_link = url_for("auth.reset_password", token=token, _external=True)
            body = (
                f"Hello {user.full_name or user.email},\n\n"
                f"Use this link to reset your password: {reset_link}\n\n"
                "If you did not request this, you can safely ignore this message."
            )
            send_email("Password Reset", email, body)
        flash("If an account exists for that email, a reset message has been sent.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        email = _normalize_email(request.form.get("email", ""))

        if not email:
            email = verify_password_reset_token(token) or ""

        if not email:
            flash("A valid email is required.", "danger")
            return redirect(url_for("auth.login"))

        if not is_gmail_address(email):
            flash(get_gmail_validation_message(), "danger")
            return redirect(url_for("auth.reset_password", token=token))

        user = _find_user_by_email(email)
        if not user or not verify_password_reset_token(token):
            flash("This password reset link is invalid or expired.", "danger")
            return redirect(url_for("auth.login"))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.reset_password", token=token))

        if not re.search(r"[A-Z]", password) or not re.search(r"[0-9]", password) or len(password) < 8:
            flash("Password must be at least 8 characters and include a number and uppercase letter.", "danger")
            return redirect(url_for("auth.reset_password", token=token))

        user.set_password(password)
        db.session.commit()
        flash("Your password has been updated successfully.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)


@auth_bp.route("/register/donor", methods=["GET", "POST"])
def donor_register():

    if request.method == "POST":
        form_data = {
            "name": (request.form.get("name") or "").strip(),
            "email": _normalize_email(request.form.get("email")),
            "phone": (request.form.get("phone") or "").strip(),
            "address": (request.form.get("address") or "").strip(),
            "organization_name": (request.form.get("organization_name") or "").strip(),
            "password": request.form.get("password") or "",
            "confirm_password": request.form.get("confirm_password") or "",
        }
        return _create_user_account(
            "donor",
            form_data,
            redirect_endpoint="auth.donor_login",
            error_endpoint="auth.donor_register",
        )

    return render_template("auth/donor_register.html")


@auth_bp.route("/register/ngo", methods=["GET", "POST"])
def ngo_register():
    if request.method == "POST":
        return _register_user("ngo", request.form)
    return render_template("auth/ngo_register.html")


@auth_bp.route("/login/donor", methods=["GET", "POST"])
def donor_login():
    form = LoginForm(meta={"csrf": False})

    if form.is_submitted() and form.email.data and form.password.data:
        user = _authenticate_user(form.email.data, form.password.data, role="donor")

        if user:
            if user.role != "donor":
                flash("Please use the donor login page.", "danger")
                return redirect(url_for("auth.donor_login"))

            remember = (request.form.get("remember") or "").lower() in {"1", "true", "yes", "y", "on"}
            login_user(user, remember=remember)
            flash("Welcome back!", "success")
            return redirect(url_for("donor.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/donor_login.html", form=form)


@auth_bp.route("/login/ngo", methods=["GET", "POST"])
def ngo_login():
    form = LoginForm(meta={"csrf": False})

    if form.is_submitted() and form.email.data and form.password.data:
        email = _normalize_email(form.email.data)
        password = form.password.data
        registration_number = (request.form.get("registration_number") or "").strip()
        
        user = None
        
        # Try to authenticate by registration_number + email + password
        if registration_number:
            ngo = NGO.query.filter_by(registration_number=registration_number).first()
            if ngo:
                ngo_user = db.session.get(User, ngo.user_id)
                if ngo_user and _normalize_email(ngo_user.email) == email and ngo_user.check_password(password):
                    user = ngo_user
        
        # Fall back to email + password authentication
        if not user:
            user = _authenticate_user(email, password, role="ngo")

        if user:
            remember = (request.form.get("remember") or "").lower() in {"1", "true", "yes", "y", "on"}
            login_user(user, remember=remember)
            flash("Welcome back!", "success")
            return redirect(url_for("ngo.dashboard"))

        flash("Invalid NGO credentials.", "danger")

    return render_template("auth/ngo_login.html", form=form)
@auth_bp.route("/login-choice")
def login_choice():
    return render_template("auth/login_choice.html")