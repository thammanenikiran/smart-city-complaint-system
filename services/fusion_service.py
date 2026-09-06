"""
Multimodal Fusion Service

Combines Text NLP analysis and Vision LLM analysis
to produce a final unified classification result.

Uses confidence-based fusion strategy:
- If text and image agree → high confidence
- If they disagree → flag for review, use higher confidence result
"""


# ==============================
# CONFIDENCE THRESHOLDS
# ==============================

AUTO_CLASSIFY_THRESHOLD = 0.80
REVIEW_THRESHOLD = 0.50


def fuse_results(
    nlp_category=None,
    nlp_confidence=0.0,
    nlp_urgency=None,
    vision_issue=None,
    vision_confidence=0.0,
    vision_severity=None
):
    """
    Combine NLP text analysis and Vision analysis results.

    Returns:
    {
        "final_category": str,
        "final_priority_input": str (severity for priority engine),
        "confidence": float,
        "source": "NLP" | "VISION" | "FUSED" | "REVIEW",
        "agreement": bool,
        "review_flag": bool,
        "reason": str
    }
    """

    has_nlp = (
        nlp_category is not None
        and nlp_category != "other"
    )

    has_vision = (
        vision_issue is not None
        and vision_issue not in ["unknown", "no_issue", None]
    )

    # ==============================
    # CASE 1: Both NLP and Vision available
    # ==============================

    if has_nlp and has_vision:

        # Normalize for comparison
        nlp_norm = nlp_category.strip().lower()
        vision_norm = vision_issue.strip().lower()

        # Check if they agree
        if nlp_norm == vision_norm:

            # Strong agreement — high confidence
            avg_confidence = (nlp_confidence + vision_confidence) / 2

            return {
                "final_category": nlp_category,
                "final_severity": vision_severity or nlp_urgency,
                "confidence": round(
                    min(avg_confidence * 1.1, 1.0), 4
                ),
                "source": "FUSED",
                "agreement": True,
                "review_flag": False,
                "reason": (
                    f"NLP and Vision agree: {nlp_category} "
                    f"(NLP: {nlp_confidence:.2f}, "
                    f"Vision: {vision_confidence:.2f})"
                )
            }

        # ==============================
        # DISAGREEMENT
        # ==============================

        # If Vision says "other" but NLP
        # identified a specific category,
        # trust the specific NLP category.
        if vision_norm == "other" and has_nlp:
            chosen_category = nlp_category
            chosen_confidence = nlp_confidence
            chosen_source = "NLP"

        # If NLP says "other" but Vision
        # identified a specific category,
        # trust Vision.
        elif nlp_norm == "other" and has_vision:
            chosen_category = vision_issue
            chosen_confidence = vision_confidence
            chosen_source = "VISION"

        # Otherwise use the higher confidence result.
        elif vision_confidence >= nlp_confidence:
            chosen_category = vision_issue
            chosen_confidence = vision_confidence
            chosen_source = "VISION"

        else:
            chosen_category = nlp_category
            chosen_confidence = nlp_confidence
            chosen_source = "NLP"

        needs_review = chosen_confidence < AUTO_CLASSIFY_THRESHOLD

        return {
            "final_category": chosen_category,
            "final_severity": vision_severity or nlp_urgency,
            "confidence": round(chosen_confidence, 4),
            "source": chosen_source,
            "agreement": False,
            "review_flag": needs_review,
            "reason": (
                f"NLP says '{nlp_category}' ({nlp_confidence:.2f}), "
                f"Vision says '{vision_issue}' ({vision_confidence:.2f}). "
                f"Using {chosen_source} result."
                + (" Flagged for review." if needs_review else "")
            )
        }

    # ==============================
    # CASE 2: Only NLP available
    # ==============================

    elif has_nlp:

        needs_review = nlp_confidence < AUTO_CLASSIFY_THRESHOLD

        return {
            "final_category": nlp_category,
            "final_severity": nlp_urgency,
            "confidence": round(nlp_confidence, 4),
            "source": "NLP",
            "agreement": False,
            "review_flag": needs_review,
            "reason": (
                f"NLP classification: {nlp_category} "
                f"({nlp_confidence:.2f}). No image provided."
            )
        }

    # ==============================
    # CASE 3: Only Vision available
    # ==============================

    elif has_vision:

        needs_review = vision_confidence < AUTO_CLASSIFY_THRESHOLD

        return {
            "final_category": vision_issue,
            "final_severity": vision_severity,
            "confidence": round(vision_confidence, 4),
            "source": "VISION",
            "agreement": False,
            "review_flag": needs_review,
            "reason": (
                f"Vision classification: {vision_issue} "
                f"({vision_confidence:.2f}). Minimal text info."
            )
        }

    # ==============================
    # CASE 4: Neither available
    # ==============================

    else:

        return {
            "final_category": "other",
            "final_severity": "MEDIUM",
            "confidence": 0.0,
            "source": "REVIEW",
            "agreement": False,
            "review_flag": True,
            "reason": "No reliable classification available. Manual review required."
        }
