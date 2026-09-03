from database.db import db


class AIResult(db.Model):
    __tablename__ = "ai_results"

    ai_result_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaints.complaint_id"),
        nullable=False
    )

    language = db.Column(
        db.String(50)
    )

    intent = db.Column(
        db.String(100)
    )

    detected_category = db.Column(
        db.String(100)
    )

    detected_sub_category = db.Column(
        db.String(100)
    )

    sentiment = db.Column(
        db.String(50)
    )

    urgency = db.Column(
        db.String(50)
    )

    summary = db.Column(
        db.Text
    )

    keywords = db.Column(
        db.Text
    )

    entities = db.Column(
        db.Text
    )

    confidence = db.Column(
        db.Numeric(5, 2)
    )

    model_name = db.Column(
        db.String(100)
    )

    language_confidence = db.Column(
        db.Numeric(5, 2)
    )

    intent_confidence = db.Column(
        db.Numeric(5, 2)
    )

    urgency_confidence = db.Column(
        db.Numeric(5, 2)
    )

    sentiment_confidence = db.Column(
        db.Numeric(5, 2)
    )

    vision_issue = db.Column(
        db.String(100)
    )

    vision_severity = db.Column(
        db.String(50)
    )

    vision_department = db.Column(
        db.String(100)
    )

    vision_description = db.Column(
        db.Text
    )

    vision_confidence = db.Column(
        db.Numeric(5, 2)
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    complaint = db.relationship(
        "Complaint",
        back_populates="ai_results"
    )