from database.db import db


class ChatHistory(db.Model):
    __tablename__ = "chat_history"

    chat_id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    response = db.Column(
        db.Text
    )

    intent = db.Column(
        db.String(100)
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp()
    )

    user = db.relationship(
        "User"
    )