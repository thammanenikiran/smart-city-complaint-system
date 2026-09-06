"""
Department Head Routes

Department Head can:
- View all complaints in their department
- Review AI classification and correct discrepancies
- Assign and reassign complaints to normal officers
- Monitor normal officer workloads
- Review resolutions, reopen, escalate, or reject complaints
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
from models.department import Department
from models.ai_result import AIResult
from models.complaint_history import ComplaintHistory
from models.feedback import Feedback
from werkzeug.security import generate_password_hash
from sqlalchemy import or_
from models.complaint_department import ComplaintDepartment

from services.assignment_service import (
    get_department_officers_workload,
    assign_complaint_to_officer
)
from services.notification_service import (
    notify_status_changed,
    notify_complaint_resolved
)


department_head_bp = Blueprint(
    "department_head",
    __name__,
    url_prefix="/department-head"
)


@department_head_bp.route("/officers")
def officers():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    current_user = User.query.get(session['user_id'])

    if current_user.role != 'OFFICER' or not current_user.is_department_head:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    officers = User.query.filter_by(
        department_id=current_user.department_id,
        role='OFFICER',
        is_department_head=False
    ).all()

    return render_template(
        'department_head/officers.html',
        officers=officers
    )


@department_head_bp.route('/officers/create', methods=['GET', 'POST'])
def create_officer():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    current_user = User.query.get(session['user_id'])

    if current_user.role != 'OFFICER' or not current_user.is_department_head:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('department_head.create_officer'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('department_head.create_officer'))

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash('An account with this email already exists.', 'danger')
            return redirect(url_for('department_head.create_officer'))

        officer = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role='OFFICER',
            department_id=current_user.department_id,
            is_department_head=False
        )

        db.session.add(officer)
        db.session.commit()

        flash('Officer created successfully.', 'success')
        return redirect(url_for('department_head.officers'))

    department = Department.query.get(current_user.department_id)

    return render_template(
        'department_head/create_officer.html',
        department=department
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


def get_authenticated_dept_head():
    """Helper to verify and return the logged-in Department Head user."""
    if "user_id" not in session:
        return None, redirect(url_for("auth.login"))

    if session.get("role") != "OFFICER":
        return None, ("Access Denied", 403)

    head = User.query.get(session["user_id"])
    if not head or not head.is_department_head:
        return None, ("Access Denied - Department Head role required", 403)

    if not head.department_id:
        return None, ("Department is not assigned to this Department Head.", 400)

    return head, None


# ==============================
# DASHBOARD
# ==============================

@department_head_bp.route("/dashboard")
def dashboard():
    head, error_response = get_authenticated_dept_head()
    if error_response:
        return error_response

    department = Department.query.get(head.department_id)
    if not department:
        return "Department not found", 404

    # ------------------------------
    # COMPLAINT STATISTICS
    # ------------------------------
    total = Complaint.query.filter_by(department_id=head.department_id).count()

    pending = Complaint.query.filter_by(
        department_id=head.department_id
    ).filter(
        Complaint.status.in_(["SUBMITTED", "AI_ANALYZING", "UNDER_REVIEW"])
    ).count()

    assigned = Complaint.query.filter_by(
        department_id=head.department_id
    ).filter(
        Complaint.status.in_(["ASSIGNED", "ACCEPTED", "IN_PROGRESS", "REOPENED", "WAITING_FOR_CITIZEN"])
    ).count()

    resolved = Complaint.query.filter_by(
        department_id=head.department_id,
        status="RESOLVED"
    ).count()

    closed = Complaint.query.filter_by(
        department_id=head.department_id,
        status="CLOSED"
    ).count()

    high_priority = Complaint.query.filter_by(
        department_id=head.department_id
    ).filter(
        Complaint.priority.in_(["HIGH", "CRITICAL"])
    ).filter(
        Complaint.status.notin_(["CLOSED", "REJECTED"])
    ).count()

    # ------------------------------
    # OFFICER WORKLOAD (Normal Officers only)
    # ------------------------------
    officers_workload = get_department_officers_workload(head.department_id)

    # ------------------------------
    # RECENT COMPLAINTS
    # ------------------------------
    recent = Complaint.query.filter_by(
        department_id=head.department_id
    ).order_by(
        Complaint.created_at.desc()
    ).limit(10).all()

    return render_template(
        "department_head/dashboard.html",
        head=head,
        department=department,
        total=total,
        pending=pending,
        assigned=assigned,
        resolved=resolved,
        closed=closed,
        high_priority=high_priority,
        officers_workload=officers_workload,
        recent=recent,
        get_status_badge=get_status_badge_class,
        get_priority_badge=get_priority_badge_class
    )


# ==============================
# ALL DEPARTMENT COMPLAINTS
# ==============================

@department_head_bp.route("/complaints")
def all_complaints():
    head, error_response = get_authenticated_dept_head()
    if error_response:
        return error_response

    status_filter = request.args.get("status")
    priority_filter = request.args.get("priority")
    officer_filter = request.args.get("officer_id")
    review_flag = request.args.get("review_flag")

    query = Complaint.query.filter(
    or_(
        Complaint.department_id == head.department_id,
        Complaint.complaint_id.in_(
            db.session.query(ComplaintDepartment.complaint_id).filter(
                ComplaintDepartment.department_id == head.department_id
            )
        )
    )
)

    if status_filter:
        query = query.filter(Complaint.status == status_filter)
    if priority_filter:
        query = query.filter(Complaint.priority == priority_filter)
    if officer_filter:
        if officer_filter == "unassigned":
            query = query.filter(Complaint.assigned_officer_id.is_(None))
        elif officer_filter.isdigit():
            query = query.filter(Complaint.assigned_officer_id == int(officer_filter))
    if review_flag == "1":
        query = query.filter(Complaint.review_flag == True)

    complaints = query.order_by(Complaint.created_at.desc()).all()
    officers = User.query.filter_by(
        department_id=head.department_id,
        role="OFFICER",
        is_department_head=False
    ).all()

    return render_template(
        "department_head/complaints.html",
        complaints=complaints,
        officers=officers,
        status_filter=status_filter,
        priority_filter=priority_filter,
        officer_filter=officer_filter,
        review_flag=review_flag,
        get_status_badge=get_status_badge_class,
        get_priority_badge=get_priority_badge_class
    )


# ==============================
# COMPLAINT DETAIL & REVIEW
# ==============================

@department_head_bp.route("/complaint/<int:complaint_id>")
def complaint_detail(complaint_id):
    head, error_response = get_authenticated_dept_head()
    if error_response:
        return error_response

    complaint = Complaint.query.get_or_404(complaint_id)

    # Security check:
    # Allow both Lead and Supporting Departments
    is_lead_department = (
        complaint.department_id == head.department_id
    )

    is_supporting_department = ComplaintDepartment.query.filter_by(
        complaint_id=complaint_id,
        department_id=head.department_id
    ).first() is not None

    if not is_lead_department and not is_supporting_department:
        flash(
            "You can only access complaints assigned to your department.",
            "danger"
        )
        return redirect(url_for("department_head.dashboard"))

    ai_result = AIResult.query.filter_by(complaint_id=complaint_id).first()

    history = ComplaintHistory.query.filter_by(
        complaint_id=complaint_id
    ).order_by(ComplaintHistory.created_at.asc()).all()

    feedback = Feedback.query.filter_by(complaint_id=complaint_id).first()

    officers_workload = get_department_officers_workload(head.department_id)
    all_departments = Department.query.order_by(Department.department_name.asc()).all()
    # Get this department's specific task for this complaint
    department_task = ComplaintDepartment.query.filter_by(
        complaint_id=complaint_id,
        department_id=head.department_id
    ).first()

    return render_template(
        "department_head/complaint_detail.html",
        complaint=complaint,
        ai_result=ai_result,
        history=history,
        feedback=feedback,
        officers_workload=officers_workload,
        departments=all_departments,
        get_status_badge=get_status_badge_class,
        get_priority_badge=get_priority_badge_class,
        department_task=department_task,
    )


@department_head_bp.route("/complaint/<int:complaint_id>/assign", methods=["POST"])
def assign_officer(complaint_id):

    head, error_response = get_authenticated_dept_head()

    if error_response:
        return error_response

    complaint = Complaint.query.get_or_404(complaint_id)

    complaint_department = ComplaintDepartment.query.filter_by(
        complaint_id=complaint_id,
        department_id=head.department_id
    ).first()

    if not complaint_department:
        flash(
            "This complaint is not assigned to your department.",
            "danger"
        )
        return redirect(
            url_for(
                "department_head.complaint_detail",
                complaint_id=complaint_id
            )
        )

    officer_id_raw = request.form.get("officer_id")
    reason = request.form.get("reason", "").strip()
    remarks = request.form.get("remarks", "").strip()

    if remarks:
        reason = f"{reason} — {remarks}" if reason else remarks

    if not officer_id_raw or not officer_id_raw.isdigit():
        flash(
            "Please select an officer from your department.",
            "danger"
        )
        return redirect(
            url_for(
                "department_head.complaint_detail",
                complaint_id=complaint_id
            )
        )

    officer_id = int(officer_id_raw)

    # Make sure officer belongs to this department
    officer = User.query.filter_by(
        user_id=officer_id,
        department_id=head.department_id,
        role="OFFICER",
        is_department_head=False
    ).first()

    if not officer:
        flash(
            "Invalid officer selected. Officer must belong to your department.",
            "danger"
        )
        return redirect(
            url_for(
                "department_head.complaint_detail",
                complaint_id=complaint_id
            )
        )

    # Prevent duplicate assignment to the same officer
    if complaint_department.assigned_officer_id == officer_id:
        flash(
            f"{officer.name} is already assigned to this department task.",
            "warning"
        )
        return redirect(
            url_for(
                "department_head.complaint_detail",
                complaint_id=complaint_id
            )
        )

    # Store previous officer before changing
    previous_officer_id = complaint_department.assigned_officer_id

    # Assign officer to this department task
    complaint_department.assigned_officer_id = officer_id
    complaint_department.status = "ASSIGNED"

    # Only the Lead Department updates the main complaint assignment
    if complaint_department.role == "LEAD":
        complaint.assigned_officer_id = officer_id

    # Create assignment/reassignment history
    if previous_officer_id:
        previous_officer = User.query.get(previous_officer_id)

        action = (
            f"{complaint_department.department.department_name} "
            f"task reassigned from "
            f"{previous_officer.name if previous_officer else 'previous officer'} "
            f"to {officer.name}"
        )

        history_status = "REASSIGNED"

    else:
        action = (
            f"{complaint_department.department.department_name} "
            f"task assigned to {officer.name}"
        )

        history_status = "ASSIGNED"

    history = ComplaintHistory(
        complaint_id=complaint_id,
        changed_by=head.user_id,
        user_role="DEPARTMENT_HEAD",
        old_status=complaint.status,
        new_status=history_status,
        action=action,
        remarks=reason or "Department-specific officer assignment"
    )

    db.session.add(history)
    db.session.commit()

    flash(
        f"Task assigned to {officer.name} successfully.",
        "success"
    )

    return redirect(
        url_for(
            "department_head.complaint_detail",
            complaint_id=complaint_id
        )
    )
    # Store previous officer before changing
    previous_officer_id = complaint_department.assigned_officer_id

    # Assign officer ONLY to this department's task
    complaint_department.assigned_officer_id = officer_id
    complaint_department.status = "ASSIGNED"

    # Keep global complaint assignment only for the Lead Department
    if complaint_department.role == "LEAD":
        complaint.assigned_officer_id = officer_id

    # Record assignment / reassignment
    if previous_officer_id:
        previous_officer = User.query.get(previous_officer_id)

        action = (
            f"{complaint_department.department.department_name} "
            f"task reassigned from "
            f"{previous_officer.name if previous_officer else 'previous officer'} "
            f"to {officer.name}"
        )
    else:
        action = (
            f"{complaint_department.department.department_name} "
            f"task assigned to {officer.name}"
        )

    history = ComplaintHistory(
        complaint_id=complaint_id,
        changed_by=head.user_id,
        user_role="DEPARTMENT_HEAD",
        old_status=complaint.status,
        new_status=complaint.status,
        action=action,
        remarks=reason or "Department-specific officer assignment"
    )

    db.session.add(history)
    db.session.commit()

    flash(
        f"Task assigned to {officer.name} successfully.",
        "success"
    )

    return redirect(
        url_for(
            "department_head.complaint_detail",
            complaint_id=complaint_id
        )
    )
# ==============================
# CORRECT AI CLASSIFICATION
# ==============================

@department_head_bp.route("/complaint/<int:complaint_id>/correct-ai", methods=["POST"])
def correct_ai(complaint_id):
    head, error_response = get_authenticated_dept_head()
    if error_response:
        return error_response

    complaint = Complaint.query.get_or_404(complaint_id)
    if complaint.department_id != head.department_id:
        flash("Unauthorized department access.", "danger")
        return redirect(url_for("department_head.dashboard"))

    new_category = request.form.get("category", "").strip()
    new_priority = request.form.get("priority", "").strip()
    target_dept_id_raw = request.form.get("department_id")
    remarks = request.form.get("remarks", "").strip()

    target_dept_id = int(target_dept_id_raw) if target_dept_id_raw and target_dept_id_raw.isdigit() else None

    # Check if transferring to another department
    if target_dept_id and target_dept_id != head.department_id:
        target_dept = Department.query.get(target_dept_id)
        if not target_dept:
            flash("Target department does not exist.", "danger")
            return redirect(url_for("department_head.complaint_detail", complaint_id=complaint_id))

        old_dept_name = complaint.department.department_name if complaint.department else "Unknown"
        complaint.department_id = target_dept_id
        complaint.assigned_officer_id = None
        complaint.review_flag = False

        if new_category:
            complaint.category = new_category
        if new_priority:
            complaint.priority = new_priority

        history = ComplaintHistory(
            complaint_id=complaint_id,
            changed_by=head.user_id,
            user_role="DEPARTMENT_HEAD",
            old_status=complaint.status,
            new_status=complaint.status,
            action=(
                f"Complaint transferred from {old_dept_name} "
                f"to {target_dept.department_name}"
            ),
            remarks=remarks or "Department reassignment by department head"
        )
        db.session.add(history)
        db.session.commit()

        flash(f"Complaint #{complaint_id} transferred to {target_dept.department_name}.", "info")
        return redirect(url_for("department_head.dashboard"))

    # Update category / priority / clear review flag
    changes = []
    if new_category and new_category != complaint.category:
        changes.append(f"Category: '{complaint.category}' -> '{new_category}'")
        complaint.category = new_category

    if new_priority and new_priority != complaint.priority:
        changes.append(f"Priority: '{complaint.priority}' -> '{new_priority}'")
        complaint.priority = new_priority

    complaint.review_flag = False

    if changes or remarks:
        action_msg = "AI classification corrected: " + ", ".join(changes) if changes else "AI classification reviewed & approved"
        history = ComplaintHistory(
            complaint_id=complaint_id,
            changed_by=head.user_id,
            user_role="DEPARTMENT_HEAD",
            old_status=complaint.status,
            new_status=complaint.status,
            action=action_msg,
            remarks=remarks
        )
        db.session.add(history)
        db.session.commit()
        flash("AI analysis review and corrections saved.", "success")
    else:
        flash("No changes were made.", "info")

    return redirect(url_for("department_head.complaint_detail", complaint_id=complaint_id))


# ==============================
# DEPARTMENT HEAD STATUS UPDATE
# ==============================

@department_head_bp.route("/complaint/<int:complaint_id>/update-status", methods=["POST"])
def update_status(complaint_id):
    head, error_response = get_authenticated_dept_head()
    if error_response:
        return error_response

    complaint = Complaint.query.get_or_404(complaint_id)
    if complaint.department_id != head.department_id:
        flash("Unauthorized department access.", "danger")
        return redirect(url_for("department_head.dashboard"))

    new_status = request.form.get("status")
    remarks = request.form.get("remarks", "").strip()

    valid_statuses = [
        "ASSIGNED", "IN_PROGRESS", "RESOLVED", "REJECTED",
        "WAITING_FOR_CITIZEN", "REOPENED", "ESCALATED", "CLOSED"
    ]

    if new_status not in valid_statuses:
        flash("Invalid status selected.", "danger")
        return redirect(url_for("department_head.complaint_detail", complaint_id=complaint_id))

    old_status = complaint.status
    complaint.status = new_status

    if new_status == "RESOLVED":
        complaint.resolved_by = head.user_id
        complaint.resolved_at = datetime.utcnow()
        complaint.resolution_description = request.form.get("resolution_description", "")
        complaint.resolution_remarks = remarks

    history = ComplaintHistory(
        complaint_id=complaint_id,
        changed_by=head.user_id,
        user_role="DEPARTMENT_HEAD",
        old_status=old_status,
        new_status=new_status,
        action=f"Status updated to {new_status} by Department Head",
        remarks=remarks
    )
    db.session.add(history)
    db.session.commit()

    try:
        if new_status == "RESOLVED":
            dept_name = complaint.department.department_name if complaint.department else "Department"
            notify_complaint_resolved(complaint.user_id, complaint_id, dept_name)
        else:
            notify_status_changed(complaint.user_id, complaint_id, new_status)
    except Exception as e:
        print(f"[WARNING] Notification error: {e}")

    flash(f"Complaint #{complaint_id} status updated to {new_status}.", "success")
    return redirect(url_for("department_head.complaint_detail", complaint_id=complaint_id))
