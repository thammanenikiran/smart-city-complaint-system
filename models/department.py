from database.db import db


class Department(db.Model):
    __tablename__ = "departments"

    department_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    department_name = db.Column(
        db.String(100),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    head_officer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id")
    )

    contact_email = db.Column(
        db.String(150)
    )

    contact_phone = db.Column(
        db.String(20)
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    complaints = db.relationship(
        "Complaint",
        back_populates="department"
    )

    def __repr__(self):
        return f"<Department {self.department_name}>"