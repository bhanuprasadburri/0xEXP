from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, IntegerField, TextAreaField, DateTimeLocalField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

from models import db, Donation
from werkzeug.utils import secure_filename
from pathlib import Path
from collections import Counter
from datetime import datetime, timedelta, timezone
import os


donor_bp = Blueprint("donor", __name__)


class DonationForm(FlaskForm):
    food_name = StringField("Food Name", validators=[DataRequired(), Length(max=150)])
    food_category = SelectField("Food Category", choices=[("Cooked", "Cooked"), ("Packed", "Packed"), ("Bakery", "Bakery"), ("Fruit", "Fruit")], validators=[DataRequired()])
    food_type = SelectField("Food Type", choices=[("Vegetarian", "Vegetarian"), ("Non-Vegetarian", "Non-Vegetarian"), ("Vegan", "Vegan")], validators=[DataRequired()])
    quantity = StringField("Quantity", validators=[DataRequired(), Length(max=50)])
    servings = IntegerField("Number of Servings", validators=[DataRequired(), NumberRange(min=1)])
    pickup_address = StringField("Pickup Address", validators=[DataRequired(), Length(max=255)])
    pickup_location = StringField("Google Maps Location")
    pickup_time = DateTimeLocalField("Pickup Time", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    expiry_time = DateTimeLocalField("Expiry Time", format="%Y-%m-%dT%H:%M", validators=[DataRequired()])
    image = FileField("Food Image", validators=[FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only!")])
    additional_notes = TextAreaField("Additional Notes")
    submit = SubmitField("Post Donation")


@donor_bp.route("/donor/dashboard")
@login_required
def dashboard():
    if current_user.role != "donor":
        flash("Access denied.", "danger")
        return redirect(url_for("public.home"))

    donations = Donation.query.filter_by(donor_id=current_user.id).order_by(Donation.created_at.desc()).all()
    completed_count = sum(1 for donation in donations if donation.status == "Completed")
    pending_count = sum(1 for donation in donations if donation.status in {"Available", "Accepted", "Collected"})
    cancelled_count = sum(1 for donation in donations if donation.status == "Cancelled")
    meals_saved = sum(donation.servings for donation in donations)
    people_impacted = meals_saved * 2
    nearby_ngos = max(3, min(12, 4 + (len(donations) % 4)))
    completion_rate = round((completed_count / len(donations) * 100), 1) if donations else 0

    category_counts = {}
    for donation in donations:
        category_counts[donation.food_category] = category_counts.get(donation.food_category, 0) + 1

    stats = [
        {"title": "Meals Donated", "value": meals_saved, "delta": "+8%", "icon": "utensils", "spark": [meals_saved] * 6},
        {"title": "Active Donations", "value": pending_count, "delta": "+3%", "icon": "package", "spark": [pending_count] * 6},
        {"title": "Completed Donations", "value": completed_count, "delta": "+5%", "icon": "check-circle-2", "spark": [completed_count] * 6},
        {"title": "People Impacted", "value": people_impacted, "delta": "+12%", "icon": "users", "spark": [people_impacted] * 6},
        {"title": "Nearby NGOs", "value": nearby_ngos, "delta": "+2%", "icon": "map-pin", "spark": [nearby_ngos] * 6},
    ]

    now = datetime.now(timezone.utc)
    monthly_labels = []
    monthly_values = []
    month_buckets = Counter()
    for donation in donations:
        if donation.created_at:
            bucket = donation.created_at.astimezone(timezone.utc).strftime("%b %Y")
            month_buckets[bucket] += 1

    for i in range(5, -1, -1):
        month = (now - timedelta(days=i * 30)).strftime("%b %Y")
        monthly_labels.append(month)
        monthly_values.append(month_buckets.get(month, 0))

    category_labels = []
    category_values = []
    category_counts = Counter(
        (donation.food_category or donation.category or "Other") for donation in donations
    )
    for category, count in category_counts.most_common():
        category_labels.append(category)
        category_values.append(count)

    activity_items = []
    for donation in donations[:4]:
        activity_items.append({
            "title": "Donation created",
            "detail": f"{donation.food_name} is now available for pickup.",
            "time": donation.created_at.strftime("%b %d"),
        })
        if donation.status in {"Accepted", "Collected", "Completed"}:
            activity_items.append({
                "title": f"{donation.status} update",
                "detail": f"Your contribution is moving through the network.",
                "time": donation.created_at.strftime("%b %d"),
            })

    if not activity_items:
        activity_items = [
            {"title": "Welcome to the workspace", "detail": "Post your first donation to start helping nearby NGOs.", "time": "Today"}
        ]

    return render_template(
        "donor/dashboard_donor.html",
        donations=donations,
        stats=stats,
        categories=category_counts,
        activity_items=activity_items,
        completion_rate=completion_rate,
        monthly_chart_labels=monthly_labels,
        monthly_chart_values=monthly_values,
        category_chart_labels=category_labels,
        category_chart_values=category_values,
    )


@donor_bp.route("/donor/add-donation", methods=["GET", "POST"])
@login_required
def add_donation():
    if current_user.role != "donor":
        flash("Access denied.", "danger")
        return redirect(url_for("public.home"))
    form = DonationForm()
    if form.validate_on_submit():
        upload_path = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            try:
                form.image.data.save(upload_path)
            except Exception:
                flash("We could not upload your image. Please try again with a different file.", "danger")
                return render_template("donor/add_donation.html", form=form)
            upload_path = filename
        donation = Donation(
            food_name=form.food_name.data,
            food_category=form.food_category.data,
            food_type=form.food_type.data,
            quantity=form.quantity.data,
            servings=form.servings.data,
            pickup_address=form.pickup_address.data,
            pickup_location=form.pickup_location.data,
            pickup_time=form.pickup_time.data,
            expiry_time=form.expiry_time.data,
            image=upload_path,
            additional_notes=form.additional_notes.data,
            donor_id=current_user.id,
        )
        db.session.add(donation)
        db.session.commit()
        flash("Donation posted successfully.", "success")
        return redirect(url_for("donor.dashboard"))
    return render_template("donor/add_donation.html", form=form)


@donor_bp.route("/donor/donations")
@login_required
def my_donations():
    if current_user.role != "donor":
        flash("Access denied.", "danger")
        return redirect(url_for("public.home"))
    donations = Donation.query.filter_by(donor_id=current_user.id).order_by(Donation.created_at.desc()).all()
    return render_template("donor/my_donations.html", donations=donations)


@donor_bp.route("/donation/<int:donation_id>")
@login_required
def donation_details(donation_id):
    donation = db.session.get(Donation, donation_id)
    if donation is None:
        return redirect(url_for("donor.dashboard"))
    return render_template("donor/donation_details.html", donation=donation)


@donor_bp.route("/donor/history")
@login_required
def donation_history():
    if current_user.role != "donor":
        flash("Access denied.", "danger")
        return redirect(url_for("public.home"))
    donations = Donation.query.filter_by(donor_id=current_user.id, status="Completed").order_by(Donation.created_at.desc()).all()
    return render_template("donor/history.html", donations=donations)
