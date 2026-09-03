from database.db import db


class Complaint(db.Model):
    __tablename__ = "complaints"

    complaint_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False
    )

    title = db.Column(
        db.String(255)
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    location = db.Column(
        db.String(255)
    )

    latitude = db.Column(
        db.Numeric(10, 7)
    )

    longitude = db.Column(
        db.Numeric(10, 7)
    )

    category = db.Column(
        db.String(100)
    )

    sub_category = db.Column(
        db.String(100)
    )

    priority = db.Column(
        db.Enum(
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL"
        ),
        default="MEDIUM"
    )

    # Using String instead of Enum for flexibility
    # with expanded status values
    status = db.Column(
        db.String(50),
        default="SUBMITTED"
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.department_id")
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    # Resolution fields
    resolution_description = db.Column(
        db.Text
    )

    resolved_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id")
    )

    resolved_at = db.Column(
        db.DateTime
    )

    resolution_remarks = db.Column(
        db.Text
    )

    # AI confidence review flag
    review_flag = db.Column(
        db.Boolean,
        default=False
    )

    # Assigned officer
    assigned_officer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id")
    )

    # Duplicate detection
    duplicate_of = db.Column(
        db.Integer,
        db.ForeignKey("complaints.complaint_id")
    )

    duplicate_score = db.Column(
        db.Numeric(5, 2)
    )

    # ==============================
    # RELATIONSHIPS
    # ==============================

    user = db.relationship(
        "User",
        back_populates="complaints",
        foreign_keys=[user_id]
    )

    department = db.relationship(
        "Department",
        back_populates="complaints"
    )

    media = db.relationship(
        "ComplaintMedia",
        back_populates="complaint",
        cascade="all, delete-orphan"
    )

    ai_results = db.relationship(
        "AIResult",
        back_populates="complaint",
        cascade="all, delete-orphan"
    )

    assignments = db.relationship(
        "ComplaintAssignment",
        back_populates="complaint",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Complaint {self.complaint_id}>"


# Valid status values for reference
COMPLAINT_STATUSES = [
    "SUBMITTED",
    "AI_ANALYZING",
    "UNDER_REVIEW",
    "ASSIGNED",
    "ACCEPTED",
    "IN_PROGRESS",
    "WAITING_FOR_CITIZEN",
    "RESOLVED",
    "RESOLUTION_REJECTED",
    "REOPENED",
    "ESCALATED",
    "CLOSED",
    "REJECTED"
]