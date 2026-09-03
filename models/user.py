from database.db import db


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    phone = db.Column(
        db.String(20)
    )

    role = db.Column(
        db.Enum(
            "CITIZEN",
            "OFFICER",
            "ADMIN"
        ),
        default="CITIZEN"
    )

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.department_id")
    )

    is_department_head = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    complaints = db.relationship(
        "Complaint",
        back_populates="user",
        foreign_keys="Complaint.user_id"
    )

    department = db.relationship(
        "Department",
        foreign_keys=[department_id]
    )

    def __repr__(self):
        return f"<User {self.email}>"