from database.db import db


class ComplaintAction(db.Model):
    __tablename__ = "complaint_actions"

    action_id = db.Column(
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
        db.ForeignKey("departments.department_id")
    )

    officer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id")
    )

    action_type = db.Column(
        db.Enum(
            "INSPECTION",
            "REPAIR",
            "CLEANING",
            "REPLACEMENT",
            "REMOVAL",
            "ROAD_WORK",
            "ELECTRICAL_REPAIR",
            "WATER_REPAIR",
            "TRAFFIC_SIGN_REPAIR",
            "TREE_REMOVAL",
            "OTHER"
        ),
        default="OTHER"
    )

    action_description = db.Column(
        db.Text
    )

    action_taken_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    remarks = db.Column(
        db.Text
    )

    proof_image_path = db.Column(
        db.String(500)
    )

    proof_video_path = db.Column(
        db.String(500)
    )

    complaint = db.relationship(
        "Complaint",
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

    def __repr__(self):
        return f"<ComplaintAction {self.action_id}>"
