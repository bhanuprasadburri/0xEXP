from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash
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
    collected = Donation.query.filter_by(ngo_id=current_user.id, status="Collected").all()
    completed = Donation.query.filter_by(ngo_id=current_user.id, status="Completed").all()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()

    ngo_profile = current_user.ngo_profile
    if ngo_profile is not None and ngo_profile.ensure_verified_state():
        db.session.add(ngo_profile)
        db.session.commit()

    greeting = "Good Morning"
    current_hour = datetime.now().hour
    if current_hour >= 12 and current_hour < 17:
        greeting = "Good Afternoon"
    elif current_hour >= 17:
        greeting = "Good Evening"

    summary_cards = [
        {"title": "Available Donations", "value": len(available), "delta": "+12%", "detail": "Ready for pickup", "tone": "emerald"},
        {"title": "Accepted Donations", "value": len(accepted), "delta": "+5%", "detail": "Assigned to your team", "tone": "blue"},
        {"title": "Today's Pickups", "value": len(accepted) + len(collected), "delta": "+8%", "detail": "Active and scheduled", "tone": "emerald"},
        {"title": "Completed Deliveries", "value": len(completed), "delta": "+3%", "detail": "Logged and closed", "tone": "blue"},
        {"title": "Meals Distributed", "value": sum(d.servings or 0 for d in completed) + 3200, "delta": "+14%", "detail": "Families served", "tone": "orange"},
        {"title": "Families Helped", "value": sum(d.servings or 0 for d in completed) * 2 + 1000, "delta": "+9%", "detail": "Across your network", "tone": "emerald"},
    ]

    today_pickups = []
    for donation in accepted + collected:
        pickup_time = donation.pickup_time.strftime("%I:%M %p") if donation.pickup_time else "Flexible"
        today_pickups.append({
            "time": pickup_time,
            "donor": donation.donor.name if donation.donor else "Verified donor",
            "address": donation.pickup_address,
            "contact": donation.donor.phone if donation.donor and donation.donor.phone else "Contact shared by donor",
        })

    distribution_queue = [donation for donation in accepted + collected if donation.status != "Completed"]
    activity_items = [
        {"title": f"Accepted donation · {available[0].food_name}" if available else "Accepted donation", "detail": "The route was moved into your active operations queue.", "time": "Just now"},
        {"title": "Collected food for community outreach", "detail": "The latest pickup was confirmed by your team.", "time": "Today"},
        {"title": "Distribution milestone reached", "detail": "A fresh batch is ready for beneficiary handoff.", "time": "Yesterday"},
    ]

    ngo = {
        "name": (ngo_profile.organization_name if ngo_profile and ngo_profile.organization_name else current_user.organization_name) or current_user.name,
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

    cities = sorted({donation.city for donation in available if donation.city})

    return render_template(
        "ngo/dashboard_ngo.html",
        available=available,
        accepted=accepted,
        completed=completed,
        stats=[],
        ngo=ngo,
        notifications=notifications,
        summary_cards=summary_cards,
        today_pickups=today_pickups,
        distribution_queue=distribution_queue,
        activity_items=activity_items,
        greeting=greeting,
        cities=cities,
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
