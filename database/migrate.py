"""
Database Migration Script

Adds new columns and tables to existing MySQL database.
Run this BEFORE starting the app if you have existing data.

Usage: python database/migrate.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database.db import db


MIGRATIONS = [
    # ==============================
    # User table: add department_id, is_department_head
    # ==============================
    "ALTER TABLE users ADD COLUMN department_id INT NULL",
    "ALTER TABLE users ADD COLUMN is_department_head TINYINT(1) DEFAULT 0",
    "ALTER TABLE users ADD CONSTRAINT fk_user_dept FOREIGN KEY (department_id) REFERENCES departments(department_id)",

    # ==============================
    # Department table: add head_officer_id, contact_email, contact_phone
    # ==============================
    "ALTER TABLE departments ADD COLUMN head_officer_id INT NULL",
    "ALTER TABLE departments ADD COLUMN contact_email VARCHAR(150) NULL",
    "ALTER TABLE departments ADD COLUMN contact_phone VARCHAR(20) NULL",

    # ==============================
    # Complaint table: change status to VARCHAR, add resolution fields
    # ==============================
    "ALTER TABLE complaints MODIFY COLUMN status VARCHAR(50) DEFAULT 'SUBMITTED'",
    "ALTER TABLE complaints ADD COLUMN resolution_description TEXT NULL",
    "ALTER TABLE complaints ADD COLUMN resolved_by INT NULL",
    "ALTER TABLE complaints ADD COLUMN resolved_at DATETIME NULL",
    "ALTER TABLE complaints ADD COLUMN resolution_remarks TEXT NULL",
    "ALTER TABLE complaints ADD COLUMN review_flag TINYINT(1) DEFAULT 0",
    "ALTER TABLE complaints ADD COLUMN assigned_officer_id INT NULL",

    # ==============================
    # AIResult table: add vision fields and confidence scores
    # ==============================
    "ALTER TABLE ai_results ADD COLUMN language_confidence DECIMAL(5,2) NULL",
    "ALTER TABLE ai_results ADD COLUMN intent_confidence DECIMAL(5,2) NULL",
    "ALTER TABLE ai_results ADD COLUMN urgency_confidence DECIMAL(5,2) NULL",
    "ALTER TABLE ai_results ADD COLUMN sentiment_confidence DECIMAL(5,2) NULL",
    "ALTER TABLE ai_results ADD COLUMN vision_issue VARCHAR(100) NULL",
    "ALTER TABLE ai_results ADD COLUMN vision_severity VARCHAR(50) NULL",
    "ALTER TABLE ai_results ADD COLUMN vision_department VARCHAR(100) NULL",
    "ALTER TABLE ai_results ADD COLUMN vision_description TEXT NULL",
    "ALTER TABLE ai_results ADD COLUMN vision_confidence DECIMAL(5,2) NULL",

    # ==============================
    # Notification table: add title, notification_type
    # ==============================
    "ALTER TABLE notifications ADD COLUMN title VARCHAR(255) NULL",
    "ALTER TABLE notifications ADD COLUMN notification_type VARCHAR(50) NULL",

    # ==============================
    # Assignment table: add officer_id, status
    # ==============================
    "ALTER TABLE complaint_assignments ADD COLUMN officer_id INT NULL",
    "ALTER TABLE complaint_assignments ADD COLUMN status ENUM('PENDING','ACCEPTED','IN_PROGRESS','COMPLETED') DEFAULT 'PENDING'",
]


def run_migrations():
    """Run all migration SQL statements."""

    with app.app_context():

        print("\n================================")
        print("DATABASE MIGRATION")
        print("================================\n")

        success = 0
        skipped = 0
        errors = 0

        for i, sql in enumerate(MIGRATIONS, 1):
            try:
                db.session.execute(db.text(sql))
                db.session.commit()
                print(f"  [{i}] OK: {sql[:70]}...")
                success += 1

            except Exception as e:
                db.session.rollback()
                error_msg = str(e)

                # Skip "duplicate column" errors
                if "Duplicate column" in error_msg or "already exists" in error_msg:
                    print(f"  [{i}] SKIP (exists): {sql[:60]}...")
                    skipped += 1
                else:
                    print(f"  [{i}] ERROR: {error_msg[:80]}")
                    errors += 1

        # Create new tables (these are handled by db.create_all)
        print("\n  Creating new tables (if not exist)...")
        db.create_all()
        print("  Done.")

        print(f"\n================================")
        print(f"  Success: {success}")
        print(f"  Skipped: {skipped}")
        print(f"  Errors:  {errors}")
        print(f"================================\n")


if __name__ == "__main__":
    run_migrations()

