from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, NGO, Donation, Notification

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/dashboard")
@login_required
def dashboard():
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("public.home"))
    users = User.query.all()
    ngos = NGO.query.all()
    donations = Donation.query.all()
    return render_template("admin/dashboard.html", users=users, ngos=ngos, donations=donations)


@admin_bp.route("/admin/approve-ngo/<int:ngo_id>", methods=["POST"])
@login_required
def approve_ngo(ngo_id):
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("public.home"))
    ngo = NGO.query.get_or_404(ngo_id)
    ngo.status = "verified"
    ngo.is_verified = True
    db.session.add(ngo)
    db.session.commit()
    flash("NGO approved successfully.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/admin/reject-ngo/<int:ngo_id>", methods=["POST"])
@login_required
def reject_ngo(ngo_id):
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("public.home"))
    ngo = NGO.query.get_or_404(ngo_id)
    ngo.status = "rejected"
    ngo.is_verified = False
    db.session.add(ngo)
    db.session.commit()
    flash("NGO rejected.", "warning")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/admin/delete-user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("public.home"))
    user = User.query.get_or_404(user_id)
    if user.role == "admin":
        flash("Cannot delete admin account.", "danger")
        return redirect(url_for("admin.dashboard"))
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully.", "success")
    return redirect(url_for("admin.dashboard"))
