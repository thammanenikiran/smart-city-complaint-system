"""
Officer Routes

Handles normal officer workflows:
- View complaints assigned to this officer
- Accept assignments and work on tasks
- Submit resolution details and remarks
"""

from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    url_for,
    request,
    flash
)

from database.db import db
from models.complaint import Complaint
from models.user import User
from models.ai_result import AIResult
from models.complaint_history import ComplaintHistory
from models.assignment import ComplaintAssignment
from services.notification_service import (
    notify_status_changed,
    notify_complaint_resolved
)


officer_bp = Blueprint(
    "officer",
    __name__,
    url_prefix="/officer"
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
        "LOW": "badge-low",
        "MEDIUM": "badge-medium",
        "HIGH": "badge-high",
        "CRITICAL": "badge-critical"
    }
    return mapping.get(priority, "bg-secondary")


def get_authenticated_officer():
    """Helper to verify and return logged-in Normal Officer."""
    if "user_id" not in session:
        return None, redirect(url_for("auth.login"))

    if session.get("role") != "OFFICER":
        return None, ("Access Denied", 403)

    # If Department Head, redirect them to department head dashboard
    if session.get("is_department_head"):
        return None, redirect(url_for("department_head.dashboard"))

    officer = User.query.get(session["user_id"])
    if not officer:
        return None, redirect(url_for("auth.login"))

    return officer, None


# ==============================
# OFFICER DASHBOARD
# ==============================

@officer_bp.route("/dashboard")
def dashboard():
    officer, error_response = get_authenticated_officer()
    if error_response:
        return error_response

    # Stats for complaints assigned directly to this officer
    assigned = Complaint.query.filter(
        Complaint.assigned_officer_id == officer.user_id,
        Complaint.status.in_(["ASSIGNED", "ACCEPTED", "IN_PROGRESS", "REOPENED", "WAITING_FOR_CITIZEN"])
    ).count()

    high_priority = Complaint.query.filter(
        Complaint.assigned_officer_id == officer.user_id,
        Complaint.priority.in_(["HIGH", "CRITICAL"]),
        Complaint.status.notin_(["CLOSED", "REJECTED"])
    ).count()

    resolved_count = Complaint.query.filter(
        Complaint.assigned_officer_id == officer.user_id,
        Complaint.status == "RESOLVED"
    ).count()

    closed_count = Complaint.query.filter(
        Complaint.assigned_officer_id == officer.user_id,
        Complaint.status == "CLOSED"
    ).count()

    recent = Complaint.query.filter(
        Complaint.assigned_officer_id == officer.user_id,
        Complaint.status.in_(["ASSIGNED", "ACCEPTED", "IN_PROGRESS", "REOPENED", "WAITING_FOR_CITIZEN"])
    ).order_by(
        Complaint.created_at.desc()
    ).limit(10).all()

    return render_template(
        "officer/dashboard.html",
        officer=officer,
        assigned=assigned,
        high_priority=high_priority,
        resolved_count=resolved_count,
        closed_count=closed_count,
        recent=recent,
        get_status_badge=get_status_badge_class,
        get_priority_badge=get_priority_badge_class
    )


# ==============================
# ASSIGNED COMPLAINTS LIST
# ==============================

@officer_bp.route("/assigned")
def assigned_complaints():
    officer, error_response = get_authenticated_officer()
    if error_response:
        return error_response

    complaints = Complaint.query.filter(
        Complaint.assigned_officer_id == officer.user_id,
        Complaint.status.in_(["ASSIGNED", "ACCEPTED", "IN_PROGRESS", "REOPENED", "WAITING_FOR_CITIZEN"])
    ).order_by(
        Complaint.created_at.desc()
    ).all()

    return render_template(
        "officer/assigned_complaints.html",
        complaints=complaints,
        get_status_badge=get_status_badge_class,
        get_priority_badge=get_priority_badge_class
    )


# ==============================
# RESOLVED COMPLAINTS LIST
# ==============================

@officer_bp.route("/resolved")
def resolved_complaints():
    officer, error_response = get_authenticated_officer()
    if error_response:
        return error_response

    complaints = Complaint.query.filter(
        Complaint.assigned_officer_id == officer.user_id,
        Complaint.status.in_(["RESOLVED", "CLOSED"])
    ).order_by(
        Complaint.updated_at.desc()
    ).all()

    return render_template(
        "officer/resolved_complaints.html",
        complaints=complaints,
        get_status_badge=get_status_badge_class,
        get_priority_badge=get_priority_badge_class
    )


# ==============================
# COMPLAINT DETAIL
# ==============================

@officer_bp.route("/complaint/<int:complaint_id>")
def complaint_detail(complaint_id):
    officer, error_response = get_authenticated_officer()
    if error_response:
        return error_response

    complaint = Complaint.query.get_or_404(complaint_id)

    # Security check: must be assigned to this officer
    if complaint.assigned_officer_id != officer.user_id:
        flash("You can only access complaints assigned directly to you.", "danger")
        return redirect(url_for("officer.dashboard"))

    ai_result = AIResult.query.filter_by(complaint_id=complaint_id).first()

    history = ComplaintHistory.query.filter_by(
        complaint_id=complaint_id
    ).order_by(
        ComplaintHistory.created_at.asc()
    ).all()

    return render_template(
        "officer/complaint_detail.html",
        complaint=complaint,
        ai_result=ai_result,
        history=history,
        get_status_badge=get_status_badge_class,
        get_priority_badge=get_priority_badge_class
    )


# ==============================
# UPDATE STATUS / RESOLVE
# ==============================

@officer_bp.route("/complaint/<int:complaint_id>/update", methods=["POST"])
def update_status(complaint_id):
    officer, error_response = get_authenticated_officer()
    if error_response:
        return error_response

    complaint = Complaint.query.get_or_404(complaint_id)

    # Security check: must be assigned to this officer
    if complaint.assigned_officer_id != officer.user_id:
        flash("You can only update complaints assigned directly to you.", "danger")
        return redirect(url_for("officer.dashboard"))

    new_status = request.form.get("status")
    remarks = request.form.get("remarks", "").strip()

    valid_statuses = [
        "ACCEPTED", "IN_PROGRESS", "RESOLVED", "WAITING_FOR_CITIZEN"
    ]

    if new_status not in valid_statuses:
        flash("Invalid status selected.", "danger")
        return redirect(url_for("officer.complaint_detail", complaint_id=complaint_id))

    old_status = complaint.status
    complaint.status = new_status

    if new_status == "RESOLVED":
        resolution_desc = request.form.get("resolution_description", "").strip()
        if not resolution_desc:
            flash("Resolution description is required when marking a complaint as resolved.", "warning")
            return redirect(url_for("officer.complaint_detail", complaint_id=complaint_id))

        complaint.resolved_by = officer.user_id
        complaint.resolved_at = datetime.utcnow()
        complaint.resolution_description = resolution_desc
        complaint.resolution_remarks = remarks

    # Update active ComplaintAssignment status
    active_assignment = ComplaintAssignment.query.filter_by(
        complaint_id=complaint_id,
        officer_id=officer.user_id
    ).order_by(ComplaintAssignment.assigned_at.desc()).first()

    if active_assignment:
        if new_status == "RESOLVED":
            active_assignment.status = "COMPLETED"
        elif new_status == "IN_PROGRESS":
            active_assignment.status = "IN_PROGRESS"
        elif new_status == "ACCEPTED":
            active_assignment.status = "ACCEPTED"

    # Add History record
    history = ComplaintHistory(
        complaint_id=complaint_id,
        changed_by=officer.user_id,
        user_role="OFFICER",
        old_status=old_status,
        new_status=new_status,
        action=f"Status updated to {new_status} by Officer {officer.name}",
        remarks=remarks or (complaint.resolution_description if new_status == "RESOLVED" else None)
    )
    db.session.add(history)
    db.session.commit()

    # Notifications
    try:
        if new_status == "RESOLVED":
            dept_name = complaint.department.department_name if complaint.department else "Department"
            notify_complaint_resolved(complaint.user_id, complaint_id, dept_name)
        else:
            notify_status_changed(complaint.user_id, complaint_id, new_status)
    except Exception as e:
        print(f"[WARNING] Notification error: {e}")

    flash(f"Complaint #{complaint_id} status updated to {new_status}.", "success")
    return redirect(url_for("officer.complaint_detail", complaint_id=complaint_id))