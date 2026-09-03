from database.db import db


class ComplaintMedia(db.Model):
    __tablename__ = "complaint_media"

    media_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    complaint_id = db.Column(
        db.Integer,
        db.ForeignKey("complaints.complaint_id"),
        nullable=False
    )

    file_name = db.Column(
        db.String(255),
        nullable=False
    )

    file_path = db.Column(
        db.String(500),
        nullable=False
    )

    file_type = db.Column(
        db.Enum("IMAGE", "VIDEO"),
        nullable=False
    )

    uploaded_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    complaint = db.relationship(
        "Complaint",
        back_populates="media"
    )