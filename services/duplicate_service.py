"""
Duplicate Detection Service

Lightweight duplicate detection for Railway deployment.
Uses text similarity instead of loading a large embedding model.
"""

from typing import Optional, Tuple
from difflib import SequenceMatcher

from models.complaint import Complaint


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two complaint descriptions.

    Returns:
        Similarity score from 0 to 100.
    """

    if not text1 or not text2:
        return 0.0

    text1 = " ".join(text1.lower().strip().split())
    text2 = " ".join(text2.lower().strip().split())

    if not text1 or not text2:
        return 0.0

    score = SequenceMatcher(None, text1, text2).ratio()

    return round(score * 100, 2)


def check_for_duplicates(
    description: str,
    exclude_complaint_id: Optional[int] = None,
    limit: int = 100,
    threshold: float = 85.0
) -> Tuple[bool, Optional[int], float]:
    """
    Check whether a complaint is similar to an existing complaint.

    Uses lightweight text similarity to avoid memory-heavy
    SentenceTransformer inference on Railway.
    """

    if not description or not description.strip():
        return False, None, 0.0

    query = Complaint.query

    if exclude_complaint_id:
        query = query.filter(
            Complaint.complaint_id != exclude_complaint_id
        )

    recent_complaints = (
        query
        .order_by(Complaint.created_at.desc())
        .limit(limit)
        .all()
    )

    if not recent_complaints:
        return False, None, 0.0

    valid_candidates = [
        complaint
        for complaint in recent_complaints
        if complaint.description
        and complaint.description.strip()
    ]

    if not valid_candidates:
        return False, None, 0.0

    best_match_id = None
    best_score = 0.0

    for candidate in valid_candidates:

        score = calculate_text_similarity(
            description,
            candidate.description
        )

        if score > best_score:
            best_score = score
            best_match_id = candidate.complaint_id

    is_duplicate = best_score >= threshold

    if is_duplicate:
        return True, best_match_id, best_score

    return False, None, best_score