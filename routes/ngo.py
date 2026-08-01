from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Donation, Notification

ngo_bp = Blueprint("ngo", __name__)


@ngo_bp.route("/ngo/dashboard")
@login_required
def dashboard():
    if current_user.role != "ngo":
        flash("Access denied.", "danger")
        return redirect(url_for("public.home"))

    available = Donation.query.filter_by(status="Available").order_by(Donation.created_at.desc()).all()
    accepted = Donation.query.filter_by(ngo_id=current_user.id, status="Accepted").all()
    completed = Donation.query.filter_by(ngo_id=current_user.id, status="Completed").all()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()

    stats = [
        {"title": "Available", "value": len(available), "delta": "+12%", "icon": "fas fa-box-open", "color": "green"},
        {"title": "Accepted", "value": len(accepted), "delta": "+5%", "icon": "fas fa-check-circle", "color": "lime"},
        {"title": "Completed", "value": len(completed), "delta": "+3%", "icon": "fas fa-truck", "color": "sky"},
        {"title": "Pickup rate", "value": 94, "delta": "Stable", "icon": "fas fa-bolt", "color": "orange"},
        {"title": "Urgent", "value": max(0, len(available) - 2), "delta": "High", "icon": "fas fa-fire", "color": "red"},
    ]

    ngo_profile = current_user.ngo_profile
    if ngo_profile is not None and ngo_profile.ensure_verified_state():
        db.session.add(ngo_profile)
        db.session.commit()
    ngo = {
        "name": current_user.organization_name or current_user.name,
        "logo": None,
        "description": "Working towards reducing food waste and supporting communities in need.",
        "location": current_user.address or "Guntur, Andhra Pradesh",
        "registration_number": ngo_profile.registration_number if ngo_profile else "REG-2024-001",
        "registration_status": "Verified" if ngo_profile and ngo_profile.is_verified else "Pending",
        "is_verified": bool(ngo_profile and ngo_profile.is_verified),
        "email": current_user.email,
        "phone": current_user.phone,
        "address": current_user.address or "Guntur, Andhra Pradesh",
        "website": "https://0xexp.org",
        "founded_year": 2023,
        "areas_served": "Guntur, Vijayawada, Nellore",
        "total_donations": len(available) + len(accepted) + len(completed),
        "meals_distributed": sum(d.servings or 0 for d in completed) + 3200,
        "people_served": sum(d.servings or 0 for d in completed) * 2 + 1000,
        "successful_pickups": len(completed),
    }

    return render_template(
        "ngo/dashboard_ngo.html",
        available=available,
        accepted=accepted,
        completed=completed,
        stats=stats,
        ngo=ngo,
        notifications=notifications,
    )


@ngo_bp.route("/ngo/accept-donation/<int:donation_id>", methods=["POST"])
@login_required
def accept_donation(donation_id):
    if current_user.role != "ngo":
        flash("Access denied.", "danger")
        return redirect(url_for("public.home"))
    donation = db.session.get(Donation, donation_id)
    if donation is None:
        flash("This donation could not be found.", "warning")
        return redirect(url_for("ngo.dashboard"))
    if donation.status != "Available":
        flash("This donation is no longer available.", "warning")
        return redirect(url_for("ngo.dashboard"))
    donation.status = "Accepted"
    donation.ngo_id = current_user.id
    db.session.add(donation)

    notification = Notification(message=f"Your donation '{donation.food_name}' has been accepted by {current_user.name}.", user_id=donation.donor_id, status="unread")
    db.session.add(notification)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        db.session.expire(donation)
        flash("We could not accept this donation right now. Please try again.", "danger")
        return redirect(url_for("ngo.dashboard"))

    flash("Donation accepted successfully.", "success")
    return redirect(url_for("ngo.dashboard"))


@ngo_bp.route("/ngo/accepted")
@login_required
def accepted_donations():
    if current_user.role != "ngo":
        flash("Access denied.", "danger")
        return redirect(url_for("public.home"))
    donations = Donation.query.filter_by(ngo_id=current_user.id).order_by(Donation.created_at.desc()).all()
    return render_template("ngo/accepted_donations.html", donations=donations)


@ngo_bp.route("/ngo/pickup-status/<int:donation_id>", methods=["POST"])
@login_required
def pickup_status(donation_id):
    if current_user.role != "ngo":
        flash("Access denied.", "danger")
        return redirect(url_for("public.home"))
    donation = db.session.get(Donation, donation_id)
    if donation is None:
        flash("This donation could not be found.", "warning")
        return redirect(url_for("ngo.accepted_donations"))
    if donation.status == "Accepted":
        donation.status = "Collected"
    elif donation.status == "Collected":
        donation.status = "Completed"
    else:
        flash("Donation already completed.", "info")
        return redirect(url_for("ngo.accepted_donations"))
    db.session.add(donation)
    db.session.commit()
    flash("Donation status updated.", "success")
    return redirect(url_for("ngo.accepted_donations"))
