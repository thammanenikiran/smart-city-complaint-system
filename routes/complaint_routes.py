"""
Complaint Routes

Handles complaint creation, viewing, tracking, resolution confirmation,
and feedback. Integrates full NLP + Vision + Fusion pipeline.
"""

import os

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    current_app
)

from werkzeug.utils import secure_filename

from database.db import db

from models.complaint import Complaint
from models.media import ComplaintMedia
from models.ai_result import AIResult
from models.complaint_history import ComplaintHistory
from models.feedback import Feedback

from services.nlp_service import analyze_complaint
from services.intent_classifier import analyze_intent_and_category
from services.ner_service import extract_entities
from services.sentiment_service import analyze_sentiment
from services.duplicate_service import check_for_duplicates
from services.department_router import assign_department
from services.priority_service import calculate_priority
from services.fusion_service import fuse_results

# Import with graceful fallback
try:
    from services.summarization_service import summarize_complaint
    SUMMARIZER_AVAILABLE = True
except Exception:
    SUMMARIZER_AVAILABLE = False

try:
    from services.vision_service import analyze_complaint_image
    VISION_AVAILABLE = True
except Exception:
    VISION_AVAILABLE = False

from services.notification_service import (
    notify_complaint_submitted,
    notify_ai_analysis_complete,
    notify_complaint_assigned,
    notify_duplicate_detected,
    notify_high_priority
)


complaint_bp = Blueprint(
    "complaint",
    __name__,
    url_prefix="/complaints"
)


UPLOAD_FOLDER = "uploads/complaints"


ALLOWED_IMAGE_EXTENSIONS = {
    "jpg", "jpeg", "png", "webp"
}


ALLOWED_VIDEO_EXTENSIONS = {
    "mp4", "avi", "mov", "mkv"
}


def allowed_image(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_IMAGE_EXTENSIONS
    )


def allowed_video(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_VIDEO_EXTENSIONS
    )


def add_history(complaint_id, user_id, role, old_status,
                new_status, action, remarks=None):
    """Helper to add complaint history entry."""

    history = ComplaintHistory(
        complaint_id=complaint_id,
        changed_by=user_id,
        user_role=role,
        old_status=old_status,
        new_status=new_status,
        action=action,
        remarks=remarks
    )
    db.session.add(history)


def get_status_badge_class(status):
    """Return CSS class for status badge."""

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
    """Return CSS class for priority badge."""

    mapping = {
        "LOW": "badge-low",
        "MEDIUM": "badge-medium",
        "HIGH": "badge-high",
        "CRITICAL": "badge-critical"
    }
    return mapping.get(priority, "bg-secondary")


# ==============================
# CREATE COMPLAINT
# ==============================

@complaint_bp.route("/create", methods=["GET", "POST"])
def create_complaint():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if session.get("role") != "CITIZEN":
        return "Access Denied", 403

    if request.method == "POST":

        title = request.form.get("title")
        description = request.form.get("description")
        location = request.form.get("location")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")

        if not description:
            flash("Complaint description is required.", "warning")
            return redirect(url_for("complaint.create_complaint"))

        # ==============================
        # CREATE COMPLAINT RECORD
        # ==============================

        complaint = Complaint(
            user_id=session["user_id"],
            title=title,
            description=description,
            location=location,
            latitude=latitude if latitude else None,
            longitude=longitude if longitude else None,
            status="SUBMITTED"
        )

        db.session.add(complaint)
        db.session.flush()

        # ==============================
        # HISTORY: SUBMITTED
        # ==============================

        add_history(
            complaint.complaint_id,
            session["user_id"],
            "CITIZEN",
            None,
            "SUBMITTED",
            "Complaint submitted by citizen"
        )

        # ==============================
        # NLP ANALYSIS
        # ==============================

        try:
            nlp_result = analyze_complaint(description)
            classification = analyze_intent_and_category(description)
            entities = extract_entities(description)
            sentiment_result = analyze_sentiment(description)

            # Summarization
            summary = None
            if SUMMARIZER_AVAILABLE:
                try:
                    summary = summarize_complaint(description)
                except Exception:
                    summary = description[:100] + "..." if len(description) > 100 else description
            else:
                summary = description[:100] + "..." if len(description) > 100 else description

        except Exception as e:
            print(f"[ERROR] NLP Analysis failed: {e}")
            nlp_result = {"language": "unknown", "keywords": []}
            classification = {
                "intent": "REPORT_ISSUE",
                "intent_confidence": 0,
                "category": "other",
                "category_confidence": 0,
                "urgency": "MEDIUM",
                "urgency_confidence": 0
            }
            entities = []
            sentiment_result = {"sentiment": "NEUTRAL", "confidence": 0}
            summary = description[:100] if description else ""

        # ==============================
        # IMAGE UPLOAD + VISION ANALYSIS
        # ==============================

        vision_result = None
        image_filepath = None

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        image = request.files.get("image")

        if image and image.filename:
            if allowed_image(image.filename):
                filename = secure_filename(image.filename)
                filename = f"{complaint.complaint_id}_image_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)

                image.save(filepath)
                image_filepath = filepath

                media = ComplaintMedia(
                    complaint_id=complaint.complaint_id,
                    file_name=filename,
                    file_path=filepath,
                    file_type="IMAGE"
                )
                db.session.add(media)

                # Gemini Vision Analysis
                if VISION_AVAILABLE:
                    try:
                        vision_result = analyze_complaint_image(filepath)
                        print(f"\n[VISION] Issue: {vision_result.get('issue')}, "
                              f"Severity: {vision_result.get('severity')}, "
                              f"Confidence: {vision_result.get('confidence')}")
                    except Exception as e:
                        print(f"[ERROR] Vision analysis failed: {e}")
                        vision_result = None

            else:
                db.session.rollback()
                flash("Invalid image format. Use JPG, PNG, or WEBP.", "danger")
                return redirect(url_for("complaint.create_complaint"))

        # ==============================
        # VIDEO UPLOAD
        # ==============================

        video = request.files.get("video")

        if video and video.filename:
            if allowed_video(video.filename):
                filename = secure_filename(video.filename)
                filename = f"{complaint.complaint_id}_video_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, filename)

                video.save(filepath)

                media = ComplaintMedia(
                    complaint_id=complaint.complaint_id,
                    file_name=filename,
                    file_path=filepath,
                    file_type="VIDEO"
                )
                db.session.add(media)

            else:
                db.session.rollback()
                flash("Invalid video format. Use MP4, AVI, MOV, or MKV.", "danger")
                return redirect(url_for("complaint.create_complaint"))

        # ==============================
        # MULTIMODAL FUSION
        # ==============================

        vision_issue = vision_result.get("issue") if vision_result else None
        vision_confidence = vision_result.get("confidence", 0) if vision_result else 0
        vision_severity = vision_result.get("severity") if vision_result else None

        fusion = fuse_results(
            nlp_category=classification["category"],
            nlp_confidence=classification["category_confidence"],
            nlp_urgency=classification["urgency"],
            vision_issue=vision_issue,
            vision_confidence=vision_confidence,
            vision_severity=vision_severity
        )

        # ==============================
        # DUPLICATE DETECTION
        # ==============================

        is_dup, duplicate_of_id, best_score = check_for_duplicates(
            description=description,
            exclude_complaint_id=complaint.complaint_id
        )

        if is_dup:
            complaint.duplicate_of = duplicate_of_id
            complaint.duplicate_score = best_score
        else:
            complaint.duplicate_of = None
            complaint.duplicate_score = None

        # ==============================
        # PRIORITY ENGINE
        # ==============================

        priority_result = calculate_priority(
            nlp_urgency=classification["urgency"],
            vision_severity=vision_severity,
            sentiment=sentiment_result["sentiment"],
            complaint_text=description,
            is_duplicate=is_dup
        )

        # ==============================
        # DEPARTMENT ASSIGNMENT
        # ==============================

        dept_result = assign_department(
            category=fusion["final_category"],
            vision_issue=vision_issue
        )

        # ==============================
        # UPDATE COMPLAINT
        # ==============================

        complaint.category = fusion["final_category"]
        complaint.priority = priority_result["priority"]
        complaint.review_flag = fusion["review_flag"]
        complaint.status = "UNDER_REVIEW" if fusion["review_flag"] else "ASSIGNED"

        if dept_result["department"]:
            complaint.department_id = dept_result["department"].department_id

        # ==============================
        # SAVE AI RESULT
        # ==============================

        ai_result = AIResult(
            complaint_id=complaint.complaint_id,
            language=nlp_result.get("language", "unknown"),
            intent=classification["intent"],
            detected_category=fusion["final_category"],
            sentiment=sentiment_result["sentiment"],
            urgency=classification["urgency"],
            summary=summary,
            keywords=", ".join(nlp_result.get("keywords", [])),
            entities=str(entities),
            confidence=round(fusion["confidence"] * 100, 2),
            model_name="BART-MNLI + BERT-NER + DistilBERT-Sentiment + Gemini-Vision",
            language_confidence=None,
            intent_confidence=round(classification["intent_confidence"] * 100, 2),
            urgency_confidence=round(classification["urgency_confidence"] * 100, 2),
            sentiment_confidence=round(sentiment_result.get("confidence", 0), 2),
            vision_issue=vision_issue,
            vision_severity=vision_severity,
            vision_department=vision_result.get("department") if vision_result else None,
            vision_description=vision_result.get("description") if vision_result else None,
            vision_confidence=round(vision_confidence * 100, 2) if vision_confidence else None
        )

        db.session.add(ai_result)

        # ==============================
        # HISTORY: AI ANALYZED + ASSIGNED
        # ==============================

        add_history(
            complaint.complaint_id,
            None, "SYSTEM",
            "SUBMITTED",
            complaint.status,
            "AI analysis completed",
            f"Category: {fusion['final_category']}, "
            f"Priority: {priority_result['priority']}, "
            f"Source: {fusion['source']}"
        )

        # ==============================
        # COMMIT
        # ==============================

        db.session.commit()

        # ==============================
        # NOTIFICATIONS (after commit)
        # ==============================

        try:
            notify_complaint_submitted(
                session["user_id"], complaint.complaint_id
            )

            notify_ai_analysis_complete(
                session["user_id"],
                complaint.complaint_id,
                fusion["final_category"]
            )

            if dept_result["department"]:
                notify_complaint_assigned(
                    session["user_id"],
                    complaint.complaint_id,
                    dept_result["department_name"]
                )

            if is_dup:
                notify_duplicate_detected(
                    session["user_id"],
                    complaint.complaint_id,
                    duplicate_of_id,
                    best_score
                )

            if priority_result["priority"] in ["HIGH", "CRITICAL"]:
                notify_high_priority(
                    session["user_id"],
                    complaint.complaint_id,
                    priority_result["priority"]
                )

        except Exception as e:
            print(f"[WARNING] Notification error: {e}")

        flash(
            f"Complaint submitted successfully! "
            f"Complaint ID: {complaint.complaint_id}",
            "success"
        )

        return redirect(url_for("complaint.my_complaints"))

    # GET request
    return render_template("complaints/create.html")


# ==============================
# MY COMPLAINTS
# ==============================

@complaint_bp.route("/my")
def my_complaints():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    complaints = Complaint.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        Complaint.created_at.desc()
    ).all()

    return render_template(
        "complaints/my_complaints.html",
        complaints=complaints,
        get_status_badge=get_status_badge_class,
        get_priority_badge=get_priority_badge_class
    )


# ==============================
# COMPLAINT DETAIL
# ==============================

@complaint_bp.route("/<int:complaint_id>")
def complaint_detail(complaint_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    complaint = Complaint.query.get_or_404(complaint_id)

    # Citizens can only view their own complaints
    if session.get("role") == "CITIZEN" and complaint.user_id != session["user_id"]:
        return "Access Denied", 403

    # Get AI result
    ai_result = AIResult.query.filter_by(
        complaint_id=complaint_id
    ).first()

    # Get history
    history = ComplaintHistory.query.filter_by(
        complaint_id=complaint_id
    ).order_by(
        ComplaintHistory.created_at.asc()
    ).all()

    # Get feedback
    feedback = Feedback.query.filter_by(
        complaint_id=complaint_id
    ).first()

    return render_template(
        "complaints/detail.html",
        complaint=complaint,
        ai_result=ai_result,
        history=history,
        feedback=feedback,
        get_status_badge=get_status_badge_class,
        get_priority_badge=get_priority_badge_class
    )


# ==============================
# CONFIRM RESOLUTION
# ==============================

@complaint_bp.route("/<int:complaint_id>/confirm", methods=["POST"])
def confirm_resolution(complaint_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.user_id != session["user_id"]:
        return "Access Denied", 403

    if complaint.status != "RESOLVED":
        flash("This complaint is not in RESOLVED status.", "warning")
        return redirect(url_for("complaint.complaint_detail", complaint_id=complaint_id))

    old_status = complaint.status
    complaint.status = "CLOSED"

    add_history(
        complaint_id, session["user_id"], "CITIZEN",
        old_status, "CLOSED",
        "Citizen confirmed resolution"
    )

    db.session.commit()

    flash("Resolution confirmed. Complaint closed.", "success")
    return redirect(url_for("complaint.complaint_detail", complaint_id=complaint_id))


# ==============================
# REJECT RESOLUTION
# ==============================

@complaint_bp.route("/<int:complaint_id>/reject", methods=["POST"])
def reject_resolution(complaint_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.user_id != session["user_id"]:
        return "Access Denied", 403

    reason = request.form.get("reason", "")

    old_status = complaint.status
    complaint.status = "REOPENED"

    add_history(
        complaint_id, session["user_id"], "CITIZEN",
        old_status, "REOPENED",
        "Citizen rejected resolution",
        reason
    )

    db.session.commit()

    flash("Complaint has been reopened for further action.", "info")
    return redirect(url_for("complaint.complaint_detail", complaint_id=complaint_id))


# ==============================
# SUBMIT FEEDBACK
# ==============================

@complaint_bp.route("/<int:complaint_id>/feedback", methods=["POST"])
def submit_feedback(complaint_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    complaint = Complaint.query.get_or_404(complaint_id)

    if complaint.user_id != session["user_id"]:
        return "Access Denied", 403

    rating = request.form.get("rating", type=int)
    comment = request.form.get("comment", "")

    if not rating or rating < 1 or rating > 5:
        flash("Please provide a valid rating (1-5).", "warning")
        return redirect(url_for("complaint.complaint_detail", complaint_id=complaint_id))

    # Check existing feedback
    existing = Feedback.query.filter_by(
        complaint_id=complaint_id,
        user_id=session["user_id"]
    ).first()

    if existing:
        existing.rating = rating
        existing.comment = comment
    else:
        feedback = Feedback(
            complaint_id=complaint_id,
            user_id=session["user_id"],
            rating=rating,
            comment=comment
        )
        db.session.add(feedback)

    db.session.commit()

    flash("Thank you for your feedback!", "success")
    return redirect(url_for("complaint.complaint_detail", complaint_id=complaint_id))