from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import db
from models.user import User


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")

        if not name or not email or not password:
            flash("Name, email and password are required.")
            return redirect(url_for("auth.register"))

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            flash("Email already registered.")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)

        user = User(
            name=name,
            email=email,
            phone=phone,
            password_hash=hashed_password,
            role="CITIZEN"
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please login.")

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(
            email=email
        ).first()

        if not user or not check_password_hash(
            user.password_hash,
            password
        ):
            flash("Invalid email or password.")
            return redirect(url_for("auth.login"))

        session["user_id"] = user.user_id
        session["user_name"] = user.name
        session["role"] = user.role
        session["is_department_head"] = bool(user.is_department_head)
        session["department_id"] = user.department_id

        if user.role == "ADMIN":
            return redirect(url_for("admin.dashboard"))

        elif user.role == "OFFICER":

            # Department Head
            if user.is_department_head:
                return redirect(url_for("department_head.dashboard"))

            # Normal Officer
            return redirect(url_for("officer.dashboard"))

        else:
            return redirect(url_for("citizen.dashboard"))

    # This is required for GET /auth/login
    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.")

    return redirect(url_for("auth.login"))