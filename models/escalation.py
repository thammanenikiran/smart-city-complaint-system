from database.db import db


class Escalation(db.Model):
    __tablename__ = "escalations"

    escalation_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaints.complaint_id"),
        nullable=False
    )

    reason = db.Column(
        db.Text,
        nullable=False
    )

    escalated_from = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id")
    )

    escalated_to = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id")
    )

    escalation_level = db.Column(
        db.Integer,
        default=1
    )

    status = db.Column(
        db.Enum(
            "OPEN",
            "RESOLVED"
        ),
        default="OPEN"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    resolved_at = db.Column(
        db.DateTime
    )

    complaint = db.relationship(
        "Complaint",
        foreign_keys=[complaint_id]
    )

    def __repr__(self):
        return f"<Escalation {self.escalation_id}>"
