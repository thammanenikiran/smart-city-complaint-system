"""
Multiple Civic Issue Detection

Detects all major civic issues mentioned in one complaint.
"""

import re


ISSUE_RULES = {
    "pothole": [
        "pothole",
        "potholes"
    ],

    "damaged_road": [
        "damaged road",
        "road damage",
        "road is damaged",
        "broken road",
        "cracked road"
    ],

    "garbage": [
        "garbage",
        "trash",
        "waste",
        "rubbish",
        "dumped waste"
    ],

    "overflowing_bin": [
        "overflowing bin",
        "overflowing bins",
        "garbage bin is full",
        "garbage bins are full",
        "bin overflow",
        "bins are overflowing"
    ],

    "water_leakage": [
        "water leakage",
        "water leak",
        "pipe is leaking",
        "water pipe is leaking",
        "leaking pipe"
    ],

    "broken_streetlight": [
        "streetlight",
        "street light",
        "street lights",
        "street lamp",
        "street lamps"
    ],

    "damaged_traffic_sign": [
        "traffic sign",
        "traffic signal",
        "traffic signals",
        "signal is not working",
        "traffic signal is not working"
    ],

    "fallen_tree": [
        "fallen tree",
        "tree has fallen",
        "tree blocking",
        "tree blocked"
    ],

    "damaged_crosswalk": [
        "crosswalk",
        "pedestrian crossing",
        "zebra crossing"
    ],

    "drainage_problem": [
        "drainage",
        "drain",
        "blocked drain",
        "drainage channel",
        "blocked drainage",
        "stagnant water",
        "waterlogging",
        "water logged",
        "water overflow"
    ]
}


def detect_multiple_issues(text):
    """
    Detect all civic issues mentioned in the complaint.

    Returns:
        list of dictionaries containing:
        category, confidence, matched_keywords
    """

    if not text:
        return []

    text_lower = text.lower()

    detected = []

    for category, keywords in ISSUE_RULES.items():

        matched_keywords = []

        for keyword in keywords:
            if re.search(
                r"\b" + re.escape(keyword) + r"\b",
                text_lower
            ):
                matched_keywords.append(keyword)

        if matched_keywords:

            detected.append({
                "category": category,
                "confidence": 0.95,
                "matched_keywords": matched_keywords
            })

    return detected
def get_department_roles(detected_issues):
    """
    Convert detected civic issues into lead/supporting departments.
    """

    ISSUE_TO_DEPARTMENT = {
        "pothole": "Roads Department",
        "damaged_road": "Roads Department",
        "damaged_crosswalk": "Roads Department",

        "garbage": "Sanitation Department",
        "overflowing_bin": "Sanitation Department",

        "water_leakage": "Water Supply Department",
        "drainage_problem": "Water Supply Department",

        "broken_streetlight": "Electrical Department",

        "damaged_traffic_sign": "Traffic Department",

        "fallen_tree": "Parks and Gardens Department",
    }

    departments = []

    for issue in detected_issues:
        category = issue["category"]

        department = ISSUE_TO_DEPARTMENT.get(category)

        if department and department not in departments:
            departments.append(department)

    result = []

    for index, department in enumerate(departments):

        result.append({
            "department_name": department,
            "role": "LEAD" if index == 0 else "SUPPORTING"
        })

    return result