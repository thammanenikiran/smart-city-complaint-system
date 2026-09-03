"""
Citizen Routes

Dashboard, complaint tracking, notifications, feedback.
"""

from flask import (
    Blueprint, render_template, session,
    redirect, url_for, request, flash
)

from database.db import db
from models.complaint import Complaint
from models.notification import Notification
from models.complaint_history import ComplaintHistory
from models.ai_result import AIResult
from services.notification_service import (
    get_user_notifications, mark_as_read, mark_all_as_read
)


citizen_bp = Blueprint(
    "citizen",
    __name__,
    url_prefix="/citizen"
)


@citizen_bp.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "CITIZEN":
        return "Access Denied", 403

    user_id = session["user_id"]

    # Stats
    total = Complaint.query.filter_by(user_id=user_id).count()

    open_count = Complaint.query.filter(
        Complaint.user_id == user_id,
        Complaint.status.notin_(["CLOSED", "REJECTED"])
    ).count()

    resolved = Complaint.query.filter_by(
        user_id=user_id, status="RESOLVED"
    ).count()

    closed = Complaint.query.filter_by(
        user_id=user_id, status="CLOSED"
    ).count()

    # Recent complaints
    recent = Complaint.query.filter_by(
        user_id=user_id
    ).order_by(
        Complaint.created_at.desc()
    ).limit(5).all()

    return render_template(
        "citizen/dashboard.html",
        total=total,
        open_count=open_count,
        resolved=resolved,
        closed=closed,
        recent=recent
    )


@citizen_bp.route("/track", methods=["GET", "POST"])
def track_complaint():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    complaint = None
    history = None
    ai_result = None

    if request.method == "POST" or request.args.get("id"):
        complaint_id = (
            request.form.get("complaint_id")
            or request.args.get("id")
        )

        if complaint_id:
            complaint = Complaint.query.filter_by(
                complaint_id=complaint_id,
                user_id=session["user_id"]
            ).first()

            if complaint:
                history = ComplaintHistory.query.filter_by(
                    complaint_id=complaint.complaint_id
                ).order_by(
                    ComplaintHistory.created_at.asc()
                ).all()

                ai_result = AIResult.query.filter_by(
                    complaint_id=complaint.complaint_id
                ).first()
            else:
                flash("Complaint not found or you don't have access.", "warning")

    return render_template(
        "citizen/track_complaint.html",
        complaint=complaint,
        history=history,
        ai_result=ai_result
    )


@citizen_bp.route("/notifications")
def notifications():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    notifs = get_user_notifications(session["user_id"])

    return render_template(
        "citizen/notifications.html",
        notifications=notifs
    )


@citizen_bp.route("/notifications/<int:notification_id>/read")
def read_notification(notification_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    notif = mark_as_read(notification_id, session["user_id"])

    if notif and notif.complaint_id:
        return redirect(url_for(
            "complaint.complaint_detail",
            complaint_id=notif.complaint_id
        ))

    return redirect(url_for("citizen.notifications"))


@citizen_bp.route("/notifications/read-all")
def read_all_notifications():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    mark_all_as_read(session["user_id"])
    flash("All notifications marked as read.", "success")
    return redirect(url_for("citizen.notifications"))