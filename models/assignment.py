from database.db import db


class ComplaintAssignment(db.Model):
    __tablename__ = "complaint_assignments"

    assignment_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaints.complaint_id"),
        nullable=False
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.department_id"),
        nullable=False
    )

    assigned_by = db.Column(
        db.String(50)
    )

    officer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id")
    )

    status = db.Column(
        db.Enum(
            "PENDING",
            "ACCEPTED",
            "IN_PROGRESS",
            "COMPLETED"
        ),
        default="PENDING"
    )

    assignment_reason = db.Column(
        db.Text
    )

    confidence = db.Column(
        db.Numeric(5, 2)
    )

    assigned_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    complaint = db.relationship(
        "Complaint",
        back_populates="assignments",
        foreign_keys=[complaint_id]
    )

    department = db.relationship(
        "Department",
        foreign_keys=[department_id]
    )

    officer = db.relationship(
        "User",
        foreign_keys=[officer_id]
    )