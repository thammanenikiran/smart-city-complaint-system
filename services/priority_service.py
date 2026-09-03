"""
Priority Service

Weighted multimodal priority engine that combines NLP urgency,
Vision severity, Sentiment, Safety indicators, and Duplicate status.
"""


# ==============================
# CONFIGURABLE WEIGHTS
# ==============================

WEIGHTS = {
    "nlp_urgency": 0.30,
    "vision_severity": 0.30,
    "sentiment": 0.15,
    "safety": 0.15,
    "duplicate": 0.10
}


# ==============================
# SAFETY KEYWORDS
# ==============================

HIGH_SAFETY_KEYWORDS = [
    "danger", "dangerous", "accident", "hazard",
    "electrical", "electrocution", "fire", "flood",
    "collapse", "collapsed", "falling", "fallen",
    "blocked", "blocking", "emergency", "urgent",
    "injury", "injured", "death", "toxic",
    "gas leak", "explosion", "sinkhole"
]

MEDIUM_SAFETY_KEYWORDS = [
    "broken", "damaged", "leaking", "overflow",
    "crack", "hole", "obstruction", "debris",
    "sharp", "exposed", "unstable"
]


def _urgency_score(urgency):
    """Convert NLP urgency label to numeric score."""

    mapping = {
        "HIGH": 1.0,
        "MEDIUM": 0.5,
        "LOW": 0.2
    }

    return mapping.get(urgency, 0.3)


def _vision_severity_score(severity):
    """Convert vision severity label to numeric score."""

    mapping = {
        "HIGH": 1.0,
        "MEDIUM": 0.5,
        "LOW": 0.2
    }

    return mapping.get(severity, 0.0)


def _sentiment_score(sentiment):
    """Convert sentiment to urgency score."""

    mapping = {
        "NEGATIVE": 0.8,
        "NEUTRAL": 0.3,
        "POSITIVE": 0.1
    }

    return mapping.get(sentiment, 0.3)


def _safety_score(text):
    """
    Analyze text for safety-critical keywords.
    Returns a score between 0 and 1.
    """

    if not text:
        return 0.0

    text_lower = text.lower()

    # Check high-priority safety keywords
    for keyword in HIGH_SAFETY_KEYWORDS:
        if keyword in text_lower:
            return 1.0

    # Check medium-priority safety keywords
    for keyword in MEDIUM_SAFETY_KEYWORDS:
        if keyword in text_lower:
            return 0.5

    return 0.0


def _duplicate_score(is_duplicate):
    """
    Duplicate complaints may indicate widespread issue.
    Higher score = more urgent (many people reporting).
    """

    return 0.7 if is_duplicate else 0.0


def _score_to_priority(score):
    """Convert weighted score to priority label."""

    if score >= 0.75:
        return "CRITICAL"

    elif score >= 0.55:
        return "HIGH"

    elif score >= 0.35:
        return "MEDIUM"

    else:
        return "LOW"


def calculate_priority(
    nlp_urgency=None,
    vision_severity=None,
    sentiment=None,
    complaint_text=None,
    is_duplicate=False
):
    """
    Calculate final priority using weighted multimodal fusion.

    Parameters:
    - nlp_urgency: "HIGH", "MEDIUM", or "LOW"
    - vision_severity: "HIGH", "MEDIUM", or "LOW"
    - sentiment: "NEGATIVE", "NEUTRAL", or "POSITIVE"
    - complaint_text: raw text for safety keyword analysis
    - is_duplicate: whether complaint is a duplicate

    Returns:
    {
        "priority": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
        "score": float (0-1),
        "breakdown": dict with individual scores
    }
    """

    # Calculate individual scores
    urgency_s = _urgency_score(nlp_urgency)
    vision_s = _vision_severity_score(vision_severity)
    sentiment_s = _sentiment_score(sentiment)
    safety_s = _safety_score(complaint_text)
    duplicate_s = _duplicate_score(is_duplicate)

    # Weighted sum
    total_score = (
        WEIGHTS["nlp_urgency"] * urgency_s +
        WEIGHTS["vision_severity"] * vision_s +
        WEIGHTS["sentiment"] * sentiment_s +
        WEIGHTS["safety"] * safety_s +
        WEIGHTS["duplicate"] * duplicate_s
    )

    # If no vision data, redistribute weight
    if vision_severity is None:
        total_score = (
            0.40 * urgency_s +
            0.20 * sentiment_s +
            0.25 * safety_s +
            0.15 * duplicate_s
        )

    priority = _score_to_priority(total_score)

    return {
        "priority": priority,
        "score": round(total_score, 3),
        "breakdown": {
            "nlp_urgency": round(urgency_s, 3),
            "vision_severity": round(vision_s, 3),
            "sentiment": round(sentiment_s, 3),
            "safety": round(safety_s, 3),
            "duplicate": round(duplicate_s, 3)
        }
    }
