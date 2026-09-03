"""
Database seed script.

Run: python database/seed.py

Creates initial departments, admin user, and sample officers.
"""

import sys
import os

# Add parent directory to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database.db import db
from models.user import User
from models.department import Department
from werkzeug.security import generate_password_hash


def seed_departments():
    """Create default departments."""

    departments = [
        {
            "department_name": "Roads Department",
            "description": "Handles potholes, damaged roads, damaged crosswalks, and road infrastructure.",
            "contact_email": "roads@smartcity.gov",
            "contact_phone": "1800-ROADS"
        },
        {
            "department_name": "Sanitation Department",
            "description": "Handles garbage collection, overflowing bins, and waste management.",
            "contact_email": "sanitation@smartcity.gov",
            "contact_phone": "1800-CLEAN"
        },
        {
            "department_name": "Water Supply Department",
            "description": "Handles water leakage, water supply issues, and drainage.",
            "contact_email": "water@smartcity.gov",
            "contact_phone": "1800-WATER"
        },
        {
            "department_name": "Electrical Department",
            "description": "Handles broken streetlights, electrical hazards, and power issues.",
            "contact_email": "electrical@smartcity.gov",
            "contact_phone": "1800-POWER"
        },
        {
            "department_name": "Traffic Department",
            "description": "Handles damaged traffic signs, traffic signal issues, and road safety.",
            "contact_email": "traffic@smartcity.gov",
            "contact_phone": "1800-TRAFFIC"
        },
        {
            "department_name": "Parks and Gardens Department",
            "description": "Handles fallen trees, park maintenance, and green spaces.",
            "contact_email": "parks@smartcity.gov",
            "contact_phone": "1800-PARKS"
        },
        {
            "department_name": "Public Health Department",
            "description": "Handles public health hazards, sanitation emergencies, and health complaints.",
            "contact_email": "health@smartcity.gov",
            "contact_phone": "1800-HEALTH"
        }
    ]

    created_count = 0

    for dept_data in departments:

        existing = Department.query.filter_by(
            department_name=dept_data["department_name"]
        ).first()

        if not existing:
            dept = Department(**dept_data)
            db.session.add(dept)
            created_count += 1
            print(f"  Created department: {dept_data['department_name']}")
        else:
            print(f"  Skipped (exists): {dept_data['department_name']}")

    db.session.commit()
    print(f"\n  Departments: {created_count} created\n")


def seed_admin():
    """Create default admin user."""

    existing = User.query.filter_by(
        email="admin@smartcity.gov"
    ).first()

    if not existing:
        admin = User(
            name="System Admin",
            email="admin@smartcity.gov",
            password_hash=generate_password_hash("admin123"),
            phone="9999999999",
            role="ADMIN"
        )
        db.session.add(admin)
        db.session.commit()
        print("  Created admin: admin@smartcity.gov / admin123")
    else:
        print("  Skipped (exists): admin@smartcity.gov")

    print()


def seed_officers():
    """Create sample officers for each department."""

    officers = [
        {
            "name": "Roads Officer",
            "email": "roads.officer@smartcity.gov",
            "department_name": "Roads Department"
        },
        {
            "name": "Sanitation Officer",
            "email": "sanitation.officer@smartcity.gov",
            "department_name": "Sanitation Department"
        },
        {
            "name": "Water Officer",
            "email": "water.officer@smartcity.gov",
            "department_name": "Water Supply Department"
        },
        {
            "name": "Electrical Officer",
            "email": "electrical.officer@smartcity.gov",
            "department_name": "Electrical Department"
        },
        {
            "name": "Traffic Officer",
            "email": "traffic.officer@smartcity.gov",
            "department_name": "Traffic Department"
        },
        {
            "name": "Parks Officer",
            "email": "parks.officer@smartcity.gov",
            "department_name": "Parks and Gardens Department"
        },
        {
            "name": "Health Officer",
            "email": "health.officer@smartcity.gov",
            "department_name": "Public Health Department"
        }
    ]

    created_count = 0

    for officer_data in officers:

        existing = User.query.filter_by(
            email=officer_data["email"]
        ).first()

        if not existing:

            dept = Department.query.filter_by(
                department_name=officer_data["department_name"]
            ).first()

            officer = User(
                name=officer_data["name"],
                email=officer_data["email"],
                password_hash=generate_password_hash("officer123"),
                phone="9000000000",
                role="OFFICER",
                department_id=dept.department_id if dept else None,
                is_department_head=True
            )

            db.session.add(officer)
            created_count += 1
            print(f"  Created officer: {officer_data['email']} / officer123")
        else:
            print(f"  Skipped (exists): {officer_data['email']}")

    db.session.commit()
    print(f"\n  Officers: {created_count} created\n")


if __name__ == "__main__":

    with app.app_context():

        print("\n================================")
        print("SMART CITY DATABASE SEED")
        print("================================\n")

        print("[1/3] Seeding departments...")
        seed_departments()

        print("[2/3] Seeding admin user...")
        seed_admin()

        print("[3/3] Seeding officers...")
        seed_officers()

        print("================================")
        print("SEED COMPLETED SUCCESSFULLY")
        print("================================\n")
