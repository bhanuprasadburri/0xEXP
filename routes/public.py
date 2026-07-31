from flask import Blueprint, render_template, request, redirect, url_for, flash

from models import db, ContactMessage
from utils.email_validation import get_gmail_validation_message, is_gmail_address

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    return render_template("public/home.html")


@public_bp.route("/about")
def about():
    return render_template("public/about.html")


@public_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        subject = (request.form.get("subject") or "").strip()
        message = (request.form.get("message") or "").strip()

        if not all([name, email, subject, message]):
            flash("Please fill in all contact fields.", "danger")
            return redirect(url_for("public.contact"))

        if not is_gmail_address(email):
            flash(get_gmail_validation_message(), "danger")
            return redirect(url_for("public.contact"))

        try:
            contact_message = ContactMessage(name=name, email=email, subject=subject, message=message)
            db.session.add(contact_message)
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("We could not save your message right now. Please try again later.", "danger")
            return redirect(url_for("public.contact"))

        flash("Response sent successfully!", "success")
        return redirect(url_for("public.contact"))

    return render_template("public/contact.html")
