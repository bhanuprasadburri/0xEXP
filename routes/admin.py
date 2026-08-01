from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, NGO, Donation, Notification, ContactMessage

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/dashboard")
@login_required
def dashboard():
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("public.home"))
    users = User.query.order_by(User.id.desc()).all()
    ngos = NGO.query.order_by(NGO.id.desc()).all()
    donations = Donation.query.order_by(Donation.id.desc()).all()
    contact_messages = ContactMessage.query.order_by(ContactMessage.id.desc()).all()
    return render_template(
        "admin/dashboard.html",
        users=users,
        ngos=ngos,
        donations=donations,
        contact_messages=contact_messages,
    )


@admin_bp.route("/admin/approve-ngo/<int:ngo_id>", methods=["POST"])
@login_required
def approve_ngo(ngo_id):
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("public.home"))
    ngo = db.session.get(NGO, ngo_id)
    if ngo is None:
        flash("This NGO could not be found.", "warning")
        return redirect(url_for("admin.dashboard"))
    ngo.status = "verified"
    ngo.is_verified = True
    db.session.add(ngo)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("We could not approve this NGO right now.", "danger")
        return redirect(url_for("admin.dashboard"))
    flash("NGO approved successfully.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/admin/reject-ngo/<int:ngo_id>", methods=["POST"])
@login_required
def reject_ngo(ngo_id):
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("public.home"))
    ngo = db.session.get(NGO, ngo_id)
    if ngo is None:
        flash("This NGO could not be found.", "warning")
        return redirect(url_for("admin.dashboard"))
    ngo.status = "rejected"
    ngo.is_verified = False
    db.session.add(ngo)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("We could not reject this NGO right now.", "danger")
        return redirect(url_for("admin.dashboard"))
    flash("NGO rejected.", "warning")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/admin/delete-user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("public.home"))
    user = db.session.get(User, user_id)
    if user is None:
        return redirect(url_for("admin.dashboard"))
    if user.role == "admin":
        flash("Cannot delete admin account.", "danger")
        return redirect(url_for("admin.dashboard"))
    db.session.delete(user)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("We could not delete this user right now.", "danger")
        return redirect(url_for("admin.dashboard"))
    flash("User deleted successfully.", "success")
    return redirect(url_for("admin.dashboard"))
