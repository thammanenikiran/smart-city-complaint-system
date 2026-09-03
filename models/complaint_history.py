from database.db import db


class ComplaintHistory(db.Model):
    __tablename__ = "complaint_history"

    history_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaints.complaint_id"),
        nullable=False
    )

    changed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id")
    )

    user_role = db.Column(
        db.String(50)
    )

    old_status = db.Column(
        db.String(50)
    )

    new_status = db.Column(
        db.String(50)
    )

    action = db.Column(
        db.String(255)
    )

    remarks = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    complaint = db.relationship(
        "Complaint",
        foreign_keys=[complaint_id]
    )

    user = db.relationship(
        "User",
        foreign_keys=[changed_by]
    )

    def __repr__(self):
        return f"<ComplaintHistory {self.history_id}>"
