from transformers import pipeline


# Load pre-trained sentiment model
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english"
)


def analyze_sentiment(text):
    """
    Analyze the sentiment of a citizen complaint.
    """

    if not text:
        return {
            "sentiment": "UNKNOWN",
            "confidence": 0
        }

    result = sentiment_pipeline(text)[0]

    return {
        "sentiment": result["label"],
        "confidence": round(
            float(result["score"]) * 100,
            2
        )
    }