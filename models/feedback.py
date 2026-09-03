from database.db import db


class Feedback(db.Model):
    __tablename__ = "feedback"

    feedback_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaints.complaint_id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False
    )

    rating = db.Column(
        db.Integer,
        nullable=False
    )

    comment = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    complaint = db.relationship(
        "Complaint"
    )

    user = db.relationship(
        "User"
    )