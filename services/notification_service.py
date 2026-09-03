"""
Notification Service

Creates and manages notifications for all complaint lifecycle events.
"""

from database.db import db
from models.notification import Notification


def create_notification(
    user_id,
    complaint_id,
    title,
    message,
    notification_type="GENERAL"
):
    """
    Create a new notification for a user.
    """

    notification = Notification(
        user_id=user_id,
        complaint_id=complaint_id,
        title=title,
        message=message,
        notification_type=notification_type,
        is_read=False
    )

    db.session.add(notification)
    db.session.commit()

    return notification


def notify_complaint_submitted(user_id, complaint_id):
    """Notify citizen that complaint was submitted."""

    return create_notification(
        user_id=user_id,
        complaint_id=complaint_id,
        title="Complaint Submitted",
        message=(
            f"Your complaint #{complaint_id} has been submitted "
            f"successfully and is being analyzed by AI."
        ),
        notification_type="COMPLAINT_SUBMITTED"
    )


def notify_ai_analysis_complete(user_id, complaint_id, category):
    """Notify citizen that AI analysis is complete."""

    return create_notification(
        user_id=user_id,
        complaint_id=complaint_id,
        title="AI Analysis Complete",
        message=(
            f"Your complaint #{complaint_id} has been analyzed. "
            f"Category: {category}."
        ),
        notification_type="AI_ANALYSIS_COMPLETE"
    )


def notify_complaint_assigned(user_id, complaint_id, department_name):
    """Notify citizen that complaint was assigned to a department."""

    return create_notification(
        user_id=user_id,
        complaint_id=complaint_id,
        title="Complaint Assigned",
        message=(
            f"Your complaint #{complaint_id} has been assigned "
            f"to the {department_name}."
        ),
        notification_type="COMPLAINT_ASSIGNED"
    )


def notify_status_changed(user_id, complaint_id, new_status):
    """Notify citizen of status change."""

    return create_notification(
        user_id=user_id,
        complaint_id=complaint_id,
        title="Status Updated",
        message=(
            f"Your complaint #{complaint_id} status has been "
            f"updated to: {new_status}."
        ),
        notification_type="STATUS_CHANGED"
    )


def notify_complaint_resolved(user_id, complaint_id, department_name):
    """Notify citizen that complaint was resolved."""

    return create_notification(
        user_id=user_id,
        complaint_id=complaint_id,
        title="Complaint Resolved",
        message=(
            f"Your complaint #{complaint_id} has been marked as "
            f"resolved by the {department_name}. "
            f"Please confirm if the issue is fixed."
        ),
        notification_type="COMPLAINT_RESOLVED"
    )


def notify_duplicate_detected(user_id, complaint_id, original_id, score):
    """Notify that a duplicate was detected."""

    return create_notification(
        user_id=user_id,
        complaint_id=complaint_id,
        title="Duplicate Detected",
        message=(
            f"Your complaint #{complaint_id} appears similar to "
            f"complaint #{original_id} (similarity: {score}%). "
            f"It has been linked for efficient processing."
        ),
        notification_type="DUPLICATE_DETECTED"
    )


def notify_high_priority(user_id, complaint_id, priority):
    """Notify about high priority complaint."""

    return create_notification(
        user_id=user_id,
        complaint_id=complaint_id,
        title="High Priority Alert",
        message=(
            f"Complaint #{complaint_id} has been classified "
            f"as {priority} priority and will be handled urgently."
        ),
        notification_type="HIGH_PRIORITY"
    )


def notify_officer_assigned(
    officer_id, complaint_id, category
):
    """Notify officer about new assignment."""

    return create_notification(
        user_id=officer_id,
        complaint_id=complaint_id,
        title="New Complaint Assigned",
        message=(
            f"Complaint #{complaint_id} ({category}) "
            f"has been assigned to you for action."
        ),
        notification_type="OFFICER_ASSIGNED"
    )


def notify_resolution_rejected(
    user_id, complaint_id, reason=None
):
    """Notify department head / officer that citizen rejected the resolution."""
    msg = f"Citizen rejected resolution for complaint #{complaint_id}. Complaint has been reopened."
    if reason:
        msg += f" Reason: {reason}"

    return create_notification(
        user_id=user_id,
        complaint_id=complaint_id,
        title="Resolution Rejected - Reopened",
        message=msg,
        notification_type="RESOLUTION_REJECTED"
    )


def notify_resolution_confirmed(
    user_id, complaint_id
):
    """Notify department head / officer that citizen confirmed the resolution."""
    return create_notification(
        user_id=user_id,
        complaint_id=complaint_id,
        title="Resolution Confirmed - Closed",
        message=f"Citizen confirmed resolution for complaint #{complaint_id}. Complaint is now closed.",
        notification_type="RESOLUTION_CONFIRMED"
    )


def get_user_notifications(user_id, limit=50):
    """Get notifications for a user."""

    return Notification.query.filter_by(
        user_id=user_id
    ).order_by(
        Notification.created_at.desc()
    ).limit(limit).all()


def get_unread_count(user_id):
    """Get unread notification count."""

    return Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).count()


def mark_as_read(notification_id, user_id):
    """Mark a notification as read."""

    notification = Notification.query.filter_by(
        notification_id=notification_id,
        user_id=user_id
    ).first()

    if notification:
        notification.is_read = True
        db.session.commit()

    return notification


def mark_all_as_read(user_id):
    """Mark all notifications as read for a user."""

    Notification.query.filter_by(
        user_id=user_id,
        is_read=False
    ).update({"is_read": True})

    db.session.commit()
