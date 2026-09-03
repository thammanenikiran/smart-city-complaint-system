from database.db import db


class Notification(db.Model):
    __tablename__ = "notifications"

    notification_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False
    )

    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaints.complaint_id")
    )

    title = db.Column(
        db.String(255)
    )

    notification_type = db.Column(
        db.String(50)
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    is_read = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    user = db.relationship(
        "User"
    )

    complaint = db.relationship(
        "Complaint"
    )