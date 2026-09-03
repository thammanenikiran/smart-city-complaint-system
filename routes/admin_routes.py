"""
Admin Routes

Dashboard with analytics, user management, department management,
complaint oversight.
"""

from flask import (
    Blueprint, render_template, session,
    redirect, url_for, request, flash
)

from database.db import db
from models.complaint import Complaint
from models.user import User
from models.department import Department
from models.ai_result import AIResult
from models.complaint_history import ComplaintHistory
from werkzeug.security import generate_password_hash

from sqlalchemy import func


admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


def get_status_badge_class(status):
    mapping = {
        "SUBMITTED": "badge-submitted",
        "AI_ANALYZING": "badge-ai-analyzing",
        "UNDER_REVIEW": "badge-under-review",
        "ASSIGNED": "badge-assigned",
        "ACCEPTED": "badge-accepted",
        "IN_PROGRESS": "badge-in-progress",
        "WAITING_FOR_CITIZEN": "badge-waiting",
        "RESOLVED": "badge-resolved",
        "RESOLUTION_REJECTED": "badge-resolution-rejected",
        "REOPENED": "badge-reopened",
        "ESCALATED": "badge-escalated",
        "CLOSED": "badge-closed",
        "REJECTED": "badge-rejected"
    }
    return mapping.get(status, "bg-secondary")


def get_priority_badge_class(priority):
    mapping = {
        "LOW": "badge-low", "MEDIUM": "badge-medium",
        "HIGH": "badge-high", "CRITICAL": "badge-critical"
    }
    return mapping.get(priority, "bg-secondary")


@admin_bp.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "ADMIN":
        return "Access Denied", 403

    # Stats
    total = Complaint.query.count()
    open_count = Complaint.query.filter(
        Complaint.status.notin_(["CLOSED", "REJECTED"])
    ).count()
    resolved = Complaint.query.filter_by(status="RESOLVED").count()
    closed = Complaint.query.filter_by(status="CLOSED").count()
    high_priority = Complaint.query.filter(
        Complaint.priority.in_(["HIGH", "CRITICAL"]),
        Complaint.status.notin_(["CLOSED", "REJECTED"])
    ).count()

    # By category
    categories = db.session.query(
        Complaint.category, func.count(Complaint.complaint_id)
    ).group_by(Complaint.category).all()

    # By department
    dept_stats = db.session.query(
        Department.department_name,
        func.count(Complaint.complaint_id)
    ).outerjoin(
        Complaint, Department.department_id == Complaint.department_id
    ).group_by(Department.department_name).all()

    # User counts
    citizen_count = User.query.filter_by(role="CITIZEN").count()
    officer_count = User.query.filter_by(role="OFFICER").count()

    # Recent complaints
    recent = Complaint.query.order_by(
        Complaint.created_at.desc()
    ).limit(10).all()

    return render_template(
        "admin/dashboard.html",
        total=total,
        open_count=open_count,
        resolved=resolved,
        closed=closed,
        high_priority=high_priority,
        categories=categories,
        dept_stats=dept_stats,
        citizen_count=citizen_count,
        officer_count=officer_count,
        recent=recent,
        get_status_badge=get_status_badge_class,
        get_priority_badge=get_priority_badge_class
    )


@admin_bp.route("/complaints")
def all_complaints():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "ADMIN":
        return "Access Denied", 403

    status_filter = request.args.get("status")
    priority_filter = request.args.get("priority")
    dept_filter = request.args.get("department")

    query = Complaint.query

    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    if dept_filter:
        query = query.filter_by(department_id=dept_filter)

    complaints = query.order_by(
        Complaint.created_at.desc()
    ).all()

    departments = Department.query.all()

    return render_template(
        "admin/complaints.html",
        complaints=complaints,
        departments=departments,
        status_filter=status_filter,
        priority_filter=priority_filter,
        dept_filter=dept_filter,
        get_status_badge=get_status_badge_class,
        get_priority_badge=get_priority_badge_class
    )


@admin_bp.route("/users")
def manage_users():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "ADMIN":
        return "Access Denied", 403

    users = User.query.order_by(User.created_at.desc()).all()
    departments = Department.query.all()

    return render_template(
        "admin/users.html",
        users=users,
        departments=departments
    )


@admin_bp.route("/users/create", methods=["POST"])
def create_user():

    if session.get("role") != "ADMIN":
        return "Access Denied", 403

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "CITIZEN").strip().upper()
    dept_id_raw = request.form.get("department_id")
    is_head_checkbox = request.form.get("is_department_head")

    if not name or not email or not password:
        flash("Name, email, and password are required.", "danger")
        return redirect(url_for("admin.manage_users"))

    existing = User.query.filter_by(email=email).first()
    if existing:
        flash(f"Email '{email}' is already registered.", "danger")
        return redirect(url_for("admin.manage_users"))

    department_id = int(dept_id_raw) if dept_id_raw and dept_id_raw.isdigit() else None

    # Determine if user is Department Head
    is_department_head = False
    if role == "DEPARTMENT_HEAD" or (role == "OFFICER" and is_head_checkbox in ["1", "true", "True", "on", "yes"]):
        is_department_head = True
        role = "OFFICER"

    # Role validation
    if role == "OFFICER":
        if not department_id:
            flash("A department is required for officers.", "danger")
            return redirect(url_for("admin.manage_users"))

        department = Department.query.get(department_id)
        if not department:
            flash("Selected department does not exist.", "danger")
            return redirect(url_for("admin.manage_users"))

        if is_department_head:
            # Check if this department already has a Department Head
            existing_head = User.query.filter_by(
                department_id=department.department_id,
                role="OFFICER",
                is_department_head=True
            ).first()

            if existing_head or department.head_officer_id:
                head_name = existing_head.name if existing_head else f"Officer ID #{department.head_officer_id}"
                flash(f"This department already has a Department Head ({head_name}). Cannot assign multiple heads.", "danger")
                return redirect(url_for("admin.manage_users"))

    else:
        # CITIZEN or ADMIN
        department_id = None
        is_department_head = False
        if role not in ["CITIZEN", "ADMIN"]:
            role = "CITIZEN"

    user = User(
        name=name,
        email=email,
        phone=phone if phone else None,
        password_hash=generate_password_hash(password),
        role=role,
        department_id=department_id,
        is_department_head=is_department_head
    )

    db.session.add(user)
    db.session.flush()

    if is_department_head and department_id:
        dept = Department.query.get(department_id)
        if dept:
            dept.head_officer_id = user.user_id

    db.session.commit()

    user_type_label = "Department Head" if is_department_head else role.capitalize()
    flash(f"{user_type_label} '{name}' ({email}) created successfully.", "success")

    return redirect(url_for("admin.manage_users"))

@admin_bp.route("/departments")
def manage_departments():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "ADMIN":
        return "Access Denied", 403

    departments = Department.query.all()

    return render_template(
        "admin/departments.html",
        departments=departments
    )


@admin_bp.route("/analytics")
def analytics():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "ADMIN":
        return "Access Denied", 403

    # Category distribution
    categories = db.session.query(
        Complaint.category, func.count(Complaint.complaint_id)
    ).group_by(Complaint.category).all()

    # Status distribution
    statuses = db.session.query(
        Complaint.status, func.count(Complaint.complaint_id)
    ).group_by(Complaint.status).all()

    # Priority distribution
    priorities = db.session.query(
        Complaint.priority, func.count(Complaint.complaint_id)
    ).group_by(Complaint.priority).all()

    # Department workload
    dept_stats = db.session.query(
        Department.department_name,
        func.count(Complaint.complaint_id)
    ).outerjoin(
        Complaint, Department.department_id == Complaint.department_id
    ).group_by(Department.department_name).all()

    total_categories = sum(c[1] for c in categories) or 1
    total_dept_stats = sum(d[1] for d in dept_stats) or 1

    return render_template(
        "admin/analytics.html",
        categories=categories,
        statuses=statuses,
        priorities=priorities,
        dept_stats=dept_stats,
        total_categories=total_categories,
        total_dept_stats=total_dept_stats,
        get_status_badge=get_status_badge_class,
        get_priority_badge=get_priority_badge_class
    )