from database.db import db
from datetime import datetime
from models.department import Department


class ComplaintDepartment(db.Model):
    __tablename__ = "complaint_departments"

    id = db.Column(db.Integer, primary_key=True)

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
    department = db.relationship(
    "Department",
    foreign_keys=[department_id]
)

    # LEAD = department coordinating the whole complaint
    # SUPPORTING = department handling one part of the complaint
    role = db.Column(
        db.String(20),
        nullable=False,
        default="SUPPORTING"
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="PENDING"
    )

    task_description = db.Column(
        db.Text,
        nullable=True
    )

    assigned_officer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    completed_at = db.Column(
        db.DateTime,
        nullable=True
    )