import os

from flask import Flask, session, send_from_directory
from dotenv import load_dotenv

from database.db import db
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from routes.citizen_routes import citizen_bp
from routes.officer_routes import officer_bp
from routes.admin_routes import admin_bp
from routes.complaint_routes import complaint_bp
from routes.department_head_routes import department_head_bp
from routes.chatbot_routes import chatbot_bp

from models import (
    User,
    Department,
    Complaint,
    ComplaintMedia,
    AIResult,
    ComplaintAssignment,
    ChatHistory,
    Feedback,
    Notification,
    ComplaintHistory,
    ComplaintAction,
    Escalation
)

load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://"
        f"{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT')}/"
        f"{os.getenv('DB_NAME')}"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Upload configuration
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB
    app.config["UPLOAD_FOLDER"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "uploads",
        "complaints"
    )

    db.init_app(app)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(citizen_bp)
    app.register_blueprint(officer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(complaint_bp)
    app.register_blueprint(department_head_bp)
    app.register_blueprint(chatbot_bp)

    # Context processor for notification count in navbar
    @app.context_processor
    def inject_notification_count():
        if "user_id" in session:
            count = Notification.query.filter_by(
                user_id=session["user_id"],
                is_read=False
            ).count()
            return {"unread_count": count}
        return {"unread_count": 0}

    # Serve uploaded media files
    @app.route("/uploads/complaints/<path:filename>")
    def serve_upload(filename):
        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            filename
        )

    return app


app = create_app()

with app.app_context():
    db.create_all()

    # Create uploads directory
    os.makedirs(
        app.config["UPLOAD_FOLDER"],
        exist_ok=True
    )


if __name__ == "__main__":
    app.run(debug=True)