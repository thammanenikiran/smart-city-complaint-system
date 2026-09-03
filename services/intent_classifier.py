try:
    from transformers import pipeline
except ImportError:
    pipeline = None


# ==========================================
# INTENT LABELS
# ==========================================

INTENT_LABELS = [
    "report a civic issue or problem",
    "request repair or maintenance",
    "report a safety hazard or danger",
    "report overflow or leakage",
    "report damage to infrastructure",
    "general query or information request"
]

INTENT_MAP = {
    "report a civic issue or problem": "REPORT_ISSUE",
    "request repair or maintenance": "REQUEST_REPAIR",
    "report a safety hazard or danger": "REPORT_HAZARD",
    "report overflow or leakage": "REPORT_OVERFLOW",
    "report damage to infrastructure": "REPORT_DAMAGE",
    "general query or information request": "GENERAL_QUERY"
}


# ==========================================
# CATEGORY LABELS
# ==========================================

CATEGORY_LABELS = [
    "pothole",
    "damaged_road",
    "water_leakage",
    "garbage",
    "overflowing_bin",
    "broken_streetlight",
    "damaged_traffic_sign",
    "fallen_tree",
    "damaged_crosswalk",
    "other"
]

CATEGORY_MAP = {
    "pothole": "pothole",
    "damaged_road": "damaged_road",
    "damaged road": "damaged_road",
    "road damage": "damaged_road",
    "water_leakage": "water_leakage",
    "water leakage": "water_leakage",
    "garbage": "garbage",
    "overflowing_bin": "overflowing_bin",
    "overflowing bin": "overflowing_bin",
    "broken_streetlight": "broken_streetlight",
    "broken streetlight": "broken_streetlight",
    "damaged_traffic_sign": "damaged_traffic_sign",
    "damaged traffic sign": "damaged_traffic_sign",
    "fallen_tree": "fallen_tree",
    "fallen tree": "fallen_tree",
    "damaged_crosswalk": "damaged_crosswalk",
    "damaged crosswalk": "damaged_crosswalk",
    "other": "other"
}


# ==========================================
# URGENCY LABELS
# ==========================================

URGENCY_LABELS = [
    "high urgency civic emergency requiring immediate action",
    "medium urgency civic problem needing attention soon",
    "low urgency routine complaint or minor issue"
]


# ==========================================
# BART MODEL
# ==========================================

classifier = None

if pipeline is not None:
    try:
        classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
    except Exception:
        classifier = None


# ==========================================
# INTENT CLASSIFICATION
# ==========================================

def classify_intent(text):

    if not text:
        return {
            "intent": "REPORT_ISSUE",
            "confidence": 0.0
        }

    if classifier is None:
        return {
            "intent": "REPORT_ISSUE",
            "confidence": 0.0
        }

    result = classifier(
        text,
        candidate_labels=INTENT_LABELS
    )

    raw_label = result["labels"][0]

    return {
        "intent": INTENT_MAP.get(
            raw_label,
            "REPORT_ISSUE"
        ),
        "confidence": round(
            result["scores"][0],
            4
        )
    }


# ==========================================
# CATEGORY CLASSIFICATION
# ==========================================

def classify_category(text):

    if not text:
        return {
            "category": "other",
            "confidence": 0.0
        }

    text_lower = text.lower().strip()


    # ==========================================
    # POTHOLE
    # ==========================================

    pothole_keywords = [
        "pothole",
        "pot hole",
        "potholes",
        "holes in the road",
        "hole in the road"
    ]

    if any(
        keyword in text_lower
        for keyword in pothole_keywords
    ):
        return {
            "category": "pothole",
            "confidence": 0.99
        }


    # ==========================================
    # ROAD DAMAGE
    # ==========================================

    road_keywords = [
        "road damage",
        "damaged road",
        "damage the road",
        "broken road",
        "road is broken",
        "road broken",
        "road surface",
        "bad road",
        "road condition",
        "road repair",
        "road needs repair",
        "crack in road",
        "cracked road",
        "road crack"
    ]

    traffic_keywords = [
        "traffic sign",
        "road sign",
        "signboard",
        "stop sign",
        "traffic signal",
        "traffic light",
        "signal light",
        "signal is not working",
        "traffic signal not working"
    ]

    if any(
        keyword in text_lower
        for keyword in road_keywords
    ):

        if not any(
            keyword in text_lower
            for keyword in traffic_keywords
        ):
            return {
                "category": "damaged_road",
                "confidence": 0.98
            }


    # ==========================================
    # WATER
    # ==========================================

    water_keywords = [
        "water leakage",
        "water leak",
        "pipe leak",
        "pipe burst",
        "water pipe",
        "water supply",
        "no water",
        "water shortage"
    ]

    if any(
        keyword in text_lower
        for keyword in water_keywords
    ):
        return {
            "category": "water_leakage",
            "confidence": 0.98
        }


    # ==========================================
    # GARBAGE
    # ==========================================

    garbage_keywords = [
        "garbage",
        "litter",
        "trash",
        "waste",
        "dustbin",
        "garbage bin",
        "overflowing bin",
        "waste bin"
    ]

    if any(
        keyword in text_lower
        for keyword in garbage_keywords
    ):

        if any(
            keyword in text_lower
            for keyword in [
                "overflowing",
                "overflow",
                "full bin"
            ]
        ):
            return {
                "category": "overflowing_bin",
                "confidence": 0.98
            }

        return {
            "category": "garbage",
            "confidence": 0.97
        }


    # ==========================================
    # STREETLIGHT
    # ==========================================

    streetlight_keywords = [
        "streetlight",
        "street light",
        "street lamp",
        "lamp post",
        "light post",
        "street light not working",
        "streetlight not working"
    ]

    if any(
        keyword in text_lower
        for keyword in streetlight_keywords
    ):
        return {
            "category": "broken_streetlight",
            "confidence": 0.98
        }


    # ==========================================
    # TRAFFIC
    # ==========================================

    traffic_keywords = [
        "traffic sign",
        "damaged traffic sign",
        "missing traffic sign",
        "broken traffic sign",
        "road sign",
        "stop sign",
        "traffic signal",
        "traffic light",
        "signal light"
    ]

    if any(
        keyword in text_lower
        for keyword in traffic_keywords
    ):
        return {
            "category": "damaged_traffic_sign",
            "confidence": 0.98
        }


    # ==========================================
    # FALLEN TREE
    # ==========================================

    tree_keywords = [
        "fallen tree",
        "fallen trees",
        "tree fallen",
        "tree has fallen",
        "tree has fallen across",
        "tree fell",
        "tree has fell",
        "tree down",
        "fallen branch",
        "fallen branches",
        "tree branch",
        "branches on road",
        "branch on road",
        "tree blocking road",
        "tree blocking the road",
        "tree across road",
        "tree across the road",
        "branches blocking road",
        "branches blocking the road"
    ]

    if any(
        keyword in text_lower
        for keyword in tree_keywords
    ):
        return {
            "category": "fallen_tree",
            "confidence": 0.99
        }


    # ==========================================
    # CROSSWALK
    # ==========================================

    crosswalk_keywords = [
        "crosswalk",
        "pedestrian crossing",
        "zebra crossing",
        "pedestrian crosswalk"
    ]

    if any(
        keyword in text_lower
        for keyword in crosswalk_keywords
    ):
        return {
            "category": "damaged_crosswalk",
            "confidence": 0.98
        }


    # ==========================================
    # BART FALLBACK
    # ==========================================

    if classifier is None:
        return {
            "category": "other",
            "confidence": 0.0
        }

    result = classifier(
        text,
        candidate_labels=CATEGORY_LABELS
    )

    raw_label = result["labels"][0]

    mapped_category = CATEGORY_MAP.get(
        raw_label,
        "other"
    )

    return {
        "category": mapped_category,
        "confidence": round(
            result["scores"][0],
            4
        )
    }


# ==========================================
# URGENCY CLASSIFICATION
# ==========================================

def classify_urgency(text):

    if not text:
        return {
            "urgency": "MEDIUM",
            "confidence": 0.0
        }

    if classifier is None:
        return {
            "urgency": "MEDIUM",
            "confidence": 0.0
        }

    result = classifier(
        text,
        candidate_labels=URGENCY_LABELS
    )

    label = result["labels"][0]
    confidence = result["scores"][0]

    if label == URGENCY_LABELS[0]:
        urgency = "HIGH"

    elif label == URGENCY_LABELS[1]:
        urgency = "MEDIUM"

    else:
        urgency = "LOW"

    return {
        "urgency": urgency,
        "confidence": round(
            confidence,
            4
        )
    }


# ==========================================
# COMPLETE ANALYSIS
# ==========================================

def analyze_intent_and_category(text):

    intent_result = classify_intent(text)

    category_result = classify_category(text)

    urgency_result = classify_urgency(text)

    return {
        "intent": intent_result["intent"],
        "intent_confidence": intent_result["confidence"],

        "category": category_result["category"],
        "category_confidence": category_result["confidence"],

        "urgency": urgency_result["urgency"],
        "urgency_confidence": urgency_result["confidence"]
    }