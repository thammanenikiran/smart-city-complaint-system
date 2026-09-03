from flask import Blueprint
from sqlalchemy import text

from database.db import db

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    try:
        db.session.execute(text("SELECT 1"))
        return "Flask + MySQL connection successful!"

    except Exception as e:
        return f"Database connection failed: {e}"