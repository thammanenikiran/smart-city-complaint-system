"""
Duplicate Detection Service

Calculates semantic similarity between a new complaint description and existing complaints
to detect duplicates and link them.
"""

from typing import Optional, List, Tuple
from models.complaint import Complaint
from services.similarity_service import embedding_model, is_duplicate, calculate_similarity
from sklearn.metrics.pairwise import cosine_similarity


def check_for_duplicates(
    description: str,
    exclude_complaint_id: Optional[int] = None,
    limit: int = 100,
    threshold: float = 85.0
) -> Tuple[bool, Optional[int], float]:
    """
    Check if a complaint description is semantically similar to recent complaints.

    Returns:
        tuple: (is_duplicate: bool, duplicate_of_id: Optional[int], best_score: float)
    """
    if not description or not description.strip():
        return False, None, 0.0

    query = Complaint.query
    if exclude_complaint_id:
        query = query.filter(Complaint.complaint_id != exclude_complaint_id)

    recent_complaints = (
        query.order_by(Complaint.created_at.desc())
        .limit(limit)
        .all()
    )

    if not recent_complaints:
        return False, None, 0.0

    valid_candidates = [
        c for c in recent_complaints if c.description and c.description.strip()
    ]

    if not valid_candidates:
        return False, None, 0.0

    try:
        # Encode target text once and all candidate descriptions in one batch for performance
        target_embedding = embedding_model.encode([description.strip()])
        candidate_texts = [c.description.strip() for c in valid_candidates]
        candidate_embeddings = embedding_model.encode(candidate_texts)

        # Compute cosine similarity
        similarities = cosine_similarity(target_embedding, candidate_embeddings)[0]

        best_idx = int(similarities.argmax())
        best_score = round(float(similarities[best_idx]) * 100, 2)
        best_match = valid_candidates[best_idx]

        is_dup = best_score >= threshold

        if is_dup:
            return True, best_match.complaint_id, best_score
        else:
            return False, None, best_score

    except Exception as e:
        print(f"[WARNING] Batch similarity detection failed: {e}. Falling back to single comparisons.")
        best_match_id = None
        best_score = 0.0

        for candidate in valid_candidates:
            try:
                score = calculate_similarity(description, candidate.description)
                if score > best_score:
                    best_score = score
                    best_match_id = candidate.complaint_id
            except Exception:
                continue

        is_dup = best_score >= threshold
        return is_dup, (best_match_id if is_dup else None), best_score
