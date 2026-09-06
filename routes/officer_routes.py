"""
Officer Routes

Handles normal officer workflows:
- View department tasks assigned to this officer
- Accept assignments and work on tasks
- Submit resolution details and remarks
- Supports multi-department complaint workflow
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
from models.complaint_department import ComplaintDepartment

from services.notification_service import (
    notify_status_changed,
    notify_complaint_resolved
)


officer_bp = Blueprint(
    "officer",
    __name__,
    url_prefix="/officer"
)


# ==============================
# BADGE HELPERS
# ==============================

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


# ==============================
# AUTHENTICATED OFFICER
# ==============================

def get_authenticated_officer():
    """Verify and return logged-in normal officer."""

    if "user_id" not in session:
        return None, redirect(url_for("auth.login"))

    if session.get("role") != "OFFICER":
        return None, ("Access Denied", 403)

    # Department Head should use Department Head dashboard
    if session.get("is_department_head"):
        return None, redirect(
            url_for("department_head.dashboard")
        )

    officer = User.query.get(session["user_id"])

    if not officer:
        return None, redirect(
            url_for("auth.login")
        )

    # Extra database-level protection
    if officer.is_department_head:
        return None, redirect(
            url_for("department_head.dashboard")
        )

    return officer, None


# ==============================
# OFFICER DASHBOARD
# ==============================

@officer_bp.route("/dashboard")
def dashboard():
    officer, error_response = get_authenticated_officer()

    if error_response:
        return error_response

    # --------------------------------
    # ACTIVE TASKS ASSIGNED TO OFFICER
    # --------------------------------
    active_tasks = ComplaintDepartment.query.filter(
        ComplaintDepartment.assigned_officer_id == officer.user_id,
        ComplaintDepartment.status.in_([
            "ASSIGNED",
            "ACCEPTED",
            "IN_PROGRESS",
            "REOPENED",
            "WAITING_FOR_CITIZEN"
        ])
    ).all()

    assigned = len(active_tasks)

    active_complaint_ids = [
        task.complaint_id
        for task in active_tasks
    ]

    # --------------------------------
    # HIGH PRIORITY TASKS
    # --------------------------------
    high_priority = 0

    if active_complaint_ids:
        high_priority = Complaint.query.filter(
            Complaint.complaint_id.in_(active_complaint_ids),
            Complaint.priority.in_(["HIGH", "CRITICAL"]),
            Complaint.status.notin_(["CLOSED", "REJECTED"])
        ).count()

    # --------------------------------
    # RESOLVED TASKS
    # --------------------------------
    resolved_tasks = ComplaintDepartment.query.filter(
        ComplaintDepartment.assigned_officer_id == officer.user_id,
        ComplaintDepartment.status == "COMPLETED"
    ).all()

    resolved_count = len(resolved_tasks)

    # --------------------------------
    # CLOSED COMPLAINTS
    # --------------------------------
    completed_complaint_ids = [
        task.complaint_id
        for task in resolved_tasks
    ]

    closed_count = 0

    if completed_complaint_ids:
        closed_count = Complaint.query.filter(
            Complaint.complaint_id.in_(completed_complaint_ids),
            Complaint.status == "CLOSED"
        ).count()

    # --------------------------------
    # RECENT ACTIVE COMPLAINTS
    # --------------------------------
    recent = []

    if active_complaint_ids:
        recent = Complaint.query.filter(
            Complaint.complaint_id.in_(active_complaint_ids)
        ).order_by(
            Complaint.created_at.desc()
        ).limit(10).all()

    # --------------------------------
    # RENDER DASHBOARD
    # --------------------------------
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
# ASSIGNED TASKS
# ==============================

@officer_bp.route("/assigned")
def assigned_complaints():

    officer, error_response = get_authenticated_officer()

    if error_response:
        return error_response

    # IMPORTANT:
    # Officer sees only department tasks specifically
    # assigned to this officer.
    tasks = (
        db.session.query(ComplaintDepartment)
        .join(
            Complaint,
            Complaint.complaint_id == ComplaintDepartment.complaint_id
        )
        .filter(
            ComplaintDepartment.assigned_officer_id == officer.user_id,
            ComplaintDepartment.status.in_([
                "ASSIGNED",
                "ACCEPTED",
                "IN_PROGRESS",
                "WAITING_FOR_CITIZEN"
            ])
        )
        .order_by(
            Complaint.created_at.desc()
        )
        .all()
    )

    # Convert tasks to complaints for compatibility
    complaints = [task for task in tasks]

    return render_template(
        "officer/assigned_complaints.html",
        complaints=complaints,
        tasks=tasks,
        get_status_badge=get_status_badge_class,
        get_priority_badge=get_priority_badge_class
    )


# ==============================
# COMPLETED / RESOLVED TASKS
# ==============================

@officer_bp.route("/resolved")
def resolved_complaints():

    officer, error_response = get_authenticated_officer()

    if error_response:
        return error_response

    tasks = (
        db.session.query(ComplaintDepartment)
        .join(
            Complaint,
            Complaint.complaint_id == ComplaintDepartment.complaint_id
        )
        .filter(
            ComplaintDepartment.assigned_officer_id == officer.user_id,
            ComplaintDepartment.status == "COMPLETED"
        )
        .order_by(
            ComplaintDepartment.completed_at.desc()
        )
        .all()
    )

    complaints = [task for task in tasks]

    return render_template(
        "officer/resolved_complaints.html",
        complaints=complaints,
        tasks=tasks,
        get_status_badge=get_status_badge_class,
        get_priority_badge=get_priority_badge_class
    )


# ==============================
# COMPLAINT / TASK DETAIL
# ==============================

@officer_bp.route("/complaint/<int:complaint_id>")
def complaint_detail(complaint_id):

    officer, error_response = get_authenticated_officer()

    if error_response:
        return error_response

    complaint = Complaint.query.get_or_404(
        complaint_id
    )

    # Find THIS officer's department-specific task
    department_task = ComplaintDepartment.query.filter_by(
        complaint_id=complaint_id,
        assigned_officer_id=officer.user_id
    ).first()

    # Security check
    if not department_task:
        flash(
            "You can only access tasks assigned directly to you.",
            "danger"
        )

        return redirect(
            url_for("officer.dashboard")
        )

    ai_result = AIResult.query.filter_by(
        complaint_id=complaint_id
    ).first()

    history = ComplaintHistory.query.filter_by(
        complaint_id=complaint_id
    ).order_by(
        ComplaintHistory.created_at.asc()
    ).all()

    return render_template(
        "officer/complaint_detail.html",
        complaint=complaint,
        department_task=department_task,
        ai_result=ai_result,
        history=history,
        get_status_badge=get_status_badge_class,
        get_priority_badge=get_priority_badge_class
    )


# ==============================
# UPDATE TASK STATUS
# ==============================

@officer_bp.route(
    "/complaint/<int:complaint_id>/update",
    methods=["POST"]
)
def update_status(complaint_id):

    officer, error_response = get_authenticated_officer()

    if error_response:
        return error_response

    complaint = Complaint.query.get_or_404(
        complaint_id
    )

    # Find this officer's department-specific task
    department_task = ComplaintDepartment.query.filter_by(
        complaint_id=complaint_id,
        assigned_officer_id=officer.user_id
    ).first()

    # Security check
    if not department_task:
        flash(
            "You can only update tasks assigned directly to you.",
            "danger"
        )

        return redirect(
            url_for("officer.dashboard")
        )

    new_status = request.form.get(
        "status"
    )

    remarks = request.form.get(
        "remarks",
        ""
    ).strip()

    valid_statuses = [
        "ACCEPTED",
        "IN_PROGRESS",
        "RESOLVED",
        "WAITING_FOR_CITIZEN"
    ]

    if new_status not in valid_statuses:

        flash(
            "Invalid status selected.",
            "danger"
        )

        return redirect(
            url_for(
                "officer.complaint_detail",
                complaint_id=complaint_id
            )
        )

    old_task_status = department_task.status

    # ==============================
    # RESOLUTION VALIDATION
    # ==============================

    resolution_desc = None

    if new_status == "RESOLVED":

        resolution_desc = request.form.get(
            "resolution_description",
            ""
        ).strip()

        if not resolution_desc:

            flash(
                "Resolution description is required when marking the task as resolved.",
                "warning"
            )

            return redirect(
                url_for(
                    "officer.complaint_detail",
                    complaint_id=complaint_id
                )
            )

    # ==============================
    # UPDATE DEPARTMENT TASK
    # ==============================

    if new_status == "RESOLVED":

        department_task.status = "COMPLETED"

        department_task.completed_at = datetime.utcnow()

    else:

        department_task.status = new_status

    # ==============================
    # LEAD DEPARTMENT
    # ==============================
    #
    # Only the Lead Department officer
    # controls the global complaint status.
    #
    # Supporting department officers update
    # only their own department task.
    # ==============================

    old_complaint_status = complaint.status

    if department_task.role == "LEAD":

        if new_status != "RESOLVED":

            complaint.status = new_status

        else:

            complaint.resolved_by = officer.user_id
            complaint.resolved_at = datetime.utcnow()

            complaint.resolution_description = resolution_desc
            complaint.resolution_remarks = remarks

            complaint.status = "RESOLVED"

    # ==============================
    # HISTORY
    # ==============================

    if new_status == "RESOLVED":

        action_text = (
            f"{department_task.department.department_name} "
            f"task completed by Officer {officer.name}"
        )

        history_remarks = (
            resolution_desc
            or remarks
        )

    else:

        action_text = (
            f"{department_task.department.department_name} "
            f"task status updated to {new_status} "
            f"by Officer {officer.name}"
        )

        history_remarks = remarks

    history = ComplaintHistory(
        complaint_id=complaint_id,
        changed_by=officer.user_id,
        user_role="OFFICER",
        old_status=old_complaint_status,
        new_status=(
            complaint.status
            if department_task.role == "LEAD"
            else new_status
        ),
        action=action_text,
        remarks=history_remarks
    )

    db.session.add(history)

    db.session.commit()

    # ==============================
    # NOTIFICATIONS
    # ==============================

    try:

        if new_status == "RESOLVED":

            dept_name = (
                department_task.department.department_name
                if department_task.department
                else "Department"
            )

            notify_complaint_resolved(
                complaint.user_id,
                complaint_id,
                dept_name
            )

        else:

            notify_status_changed(
                complaint.user_id,
                complaint_id,
                new_status
            )

    except Exception as e:

        print(
            f"[WARNING] Notification error: {e}"
        )

    # ==============================
    # SUCCESS MESSAGE
    # ==============================

    if new_status == "RESOLVED":

        flash(
            f"{department_task.department.department_name} "
            f"task completed successfully.",
            "success"
        )

    else:

        flash(
            f"Task status updated to {new_status}.",
            "success"
        )

    return redirect(
        url_for(
            "officer.complaint_detail",
            complaint_id=complaint_id
        )
    )