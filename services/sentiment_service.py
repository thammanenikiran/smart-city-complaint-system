from transformers import pipeline

sentiment_pipeline = None


def get_sentiment_pipeline():
    global sentiment_pipeline

    if sentiment_pipeline is None:
        sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )

    return sentiment_pipeline


def analyze_sentiment(text):
    """
    Analyze the sentiment of a citizen complaint.
    """

    if not text:
        return {
            "sentiment": "UNKNOWN",
            "confidence": 0
        }

    result = get_sentiment_pipeline()(text)[0]

    return {
        "sentiment": result["label"],
        "confidence": round(
            float(result["score"]) * 100,
            2
        )
    }