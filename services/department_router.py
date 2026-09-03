"""
Department Router Service

Maps complaint categories (from NLP and Vision) to departments.
Centralized department assignment logic.
"""

from models.department import Department


# ==============================
# CATEGORY TO DEPARTMENT MAPPING
# ==============================

CATEGORY_TO_DEPARTMENT = {

    # NLP category labels
    "pothole": "Roads Department",
    "damaged_road": "Roads Department",
    "damaged_crosswalk": "Roads Department",

    "garbage": "Sanitation Department",
    "overflowing_bin": "Sanitation Department",

    "water_leakage": "Water Supply Department",

    "broken_streetlight": "Electrical Department",

    "damaged_traffic_sign": "Traffic Department",

    "fallen_tree": "Parks and Gardens Department",

    # Legacy NLP labels (backward compatibility)
    "road damage": "Roads Department",
    "waste management": "Sanitation Department",
    "water supply": "Water Supply Department",
    "electrical problem": "Electrical Department",
    "drainage problem": "Water Supply Department",
    "traffic problem": "Traffic Department",
    "public health problem": "Public Health Department"
}


# ==============================
# VISION ISSUE TO DEPARTMENT
# ==============================

VISION_TO_DEPARTMENT = {
    "pothole": "Roads Department",
    "damaged_road": "Roads Department",
    "garbage": "Sanitation Department",
    "overflowing_bin": "Sanitation Department",
    "broken_streetlight": "Electrical Department",
    "water_leakage": "Water Supply Department",
    "damaged_traffic_sign": "Traffic Department",
    "fallen_tree": "Parks and Gardens Department",
    "damaged_crosswalk": "Roads Department"
}


def normalize_category(category):
    """
    Convert the AI category into a standard format.
    """

    if not category:
        return ""

    return category.strip().lower()


def find_department(category):
    """
    Find the department corresponding
    to the detected complaint category.
    """

    normalized = normalize_category(category)

    department_name = CATEGORY_TO_DEPARTMENT.get(normalized)

    if not department_name:
        return None

    department = Department.query.filter_by(
        department_name=department_name
    ).first()

    return department


def find_department_by_vision(vision_issue):
    """
    Find department based on vision analysis result.
    """

    if not vision_issue:
        return None

    normalized = vision_issue.strip().lower()

    department_name = VISION_TO_DEPARTMENT.get(normalized)

    if not department_name:
        return None

    department = Department.query.filter_by(
        department_name=department_name
    ).first()

    return department


def assign_department(category, vision_issue=None):
    """
    Assign a department based on NLP category and/or vision result.

    Tries vision-based assignment first (usually more specific),
    then falls back to NLP category.
    """

    department = None
    source = None

    # Try vision-based assignment first
    if vision_issue and vision_issue not in ["unknown", "no_issue"]:
        department = find_department_by_vision(vision_issue)
        if department:
            source = "VISION_AI"

    # Fall back to NLP category
    if not department and category:
        department = find_department(category)
        if department:
            source = "NLP_AI"

    if not department:
        return {
            "department": None,
            "department_name": None,
            "reason": "No matching department found.",
            "source": "NONE",
            "confidence": 0
        }

    return {
        "department": department,
        "department_name": department.department_name,
        "reason": (
            f"Category '{category}' mapped to "
            f"'{department.department_name}' via {source}."
        ),
        "source": source,
        "confidence": 100
    }


def get_department_name_for_category(category):
    """
    Get department name string without DB lookup.
    Useful when DB context is not available.
    """

    normalized = normalize_category(category)
    return CATEGORY_TO_DEPARTMENT.get(normalized, "Manual Review")