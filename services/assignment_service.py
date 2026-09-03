"""
Complaint Assignment Service

Manages assignment of complaints to normal officers by Department Heads,
tracks assignments, and calculates officer workload metrics.
"""

from typing import Tuple, List, Dict, Any, Optional
from database.db import db
from models.complaint import Complaint
from models.user import User
from models.department import Department
from models.assignment import ComplaintAssignment
from models.complaint_history import ComplaintHistory
from services.notification_service import (
    notify_officer_assigned,
    notify_status_changed
)


def get_department_officers_workload(department_id: int) -> List[Dict[str, Any]]:
    """
    Get all normal officers (excluding department head) in a department with workload stats.
    """
    if not department_id:
        return []

    officers = User.query.filter_by(
        department_id=department_id,
        role="OFFICER",
        is_department_head=False
    ).order_by(User.name.asc()).all()

    workload_list = []

    for officer in officers:
        assigned_count = Complaint.query.filter(
            Complaint.assigned_officer_id == officer.user_id,
            Complaint.status.in_(["ASSIGNED", "ACCEPTED", "REOPENED", "WAITING_FOR_CITIZEN"])
        ).count()

        in_progress_count = Complaint.query.filter(
            Complaint.assigned_officer_id == officer.user_id,
            Complaint.status == "IN_PROGRESS"
        ).count()

        resolved_count = Complaint.query.filter(
            Complaint.assigned_officer_id == officer.user_id,
            Complaint.status.in_(["RESOLVED", "CLOSED"])
        ).count()

        active_workload = assigned_count + in_progress_count

        workload_list.append({
            "officer": officer,
            "officer_id": officer.user_id,
            "name": officer.name,
            "email": officer.email,
            "phone": officer.phone,
            "assigned": assigned_count,
            "in_progress": in_progress_count,
            "resolved": resolved_count,
            "active_workload": active_workload
        })

    return workload_list


def assign_complaint_to_officer(
    complaint_id: int,
    officer_id: int,
    assigned_by_user_id: int,
    reason: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Assign a complaint to a normal officer in the same department.
    """
    complaint = Complaint.query.get(complaint_id)
    if not complaint:
        return False, "Complaint not found."

    officer = User.query.get(officer_id)
    if not officer:
        return False, "Selected officer not found."

    if officer.role != "OFFICER" or officer.is_department_head:
        return False, "Complaints can only be assigned to normal officers."

    if officer.department_id != complaint.department_id:
        return False, "Officer does not belong to the same department as this complaint."

    assigner = User.query.get(assigned_by_user_id)
    assigner_name = assigner.name if assigner else "Department Head"

    old_status = complaint.status
    old_officer_id = complaint.assigned_officer_id

    # Update complaint
    complaint.assigned_officer_id = officer.user_id
    if complaint.status in ["SUBMITTED", "AI_ANALYZING", "UNDER_REVIEW", "REOPENED"]:
        complaint.status = "ASSIGNED"

    # Close previous active assignments for this complaint
    previous_assignments = ComplaintAssignment.query.filter_by(
        complaint_id=complaint_id
    ).filter(
        ComplaintAssignment.status.in_(["PENDING", "ACCEPTED", "IN_PROGRESS"])
    ).all()

    for pa in previous_assignments:
        pa.status = "COMPLETED"

    # Create new assignment
    new_assignment = ComplaintAssignment(
        complaint_id=complaint_id,
        department_id=complaint.department_id,
        assigned_by=assigner_name,
        officer_id=officer.user_id,
        status="PENDING",
        assignment_reason=reason or "Assigned by Department Head"
    )
    db.session.add(new_assignment)

    # Record complaint history
    reassignment_text = "Reassigned" if old_officer_id and old_officer_id != officer.user_id else "Assigned"
    action_text = f"{reassignment_text} to Officer {officer.name}"

    history = ComplaintHistory(
        complaint_id=complaint_id,
        changed_by=assigned_by_user_id,
        user_role="DEPARTMENT_HEAD",
        old_status=old_status,
        new_status=complaint.status,
        action=action_text,
        remarks=reason
    )
    db.session.add(history)
    db.session.commit()

    # Send notifications
    try:
        notify_officer_assigned(
            officer.user_id,
            complaint_id,
            complaint.category or "Civic Complaint"
        )
        notify_status_changed(
            complaint.user_id,
            complaint_id,
            f"Assigned to {officer.name} ({complaint.department.department_name if complaint.department else 'Department'})"
        )
    except Exception as e:
        print(f"[WARNING] Notification failed during assignment: {e}")

    return True, f"Complaint #{complaint_id} assigned to {officer.name}."
