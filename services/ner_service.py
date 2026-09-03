from transformers import pipeline


# Load pre-trained BERT NER model
ner_pipeline = pipeline(
    "ner",
    model="dslim/bert-base-NER",
    aggregation_strategy="simple"
)


def extract_entities(text):
    """
    Extract named entities from complaint text.
    """

    if not text:
        return []

    results = ner_pipeline(text)

    entities = []

    for result in results:

        entities.append({
            "text": result["word"],
            "label": result["entity_group"],
            "confidence": round(
                float(result["score"]) * 100,
                2
            )
        })

    return entities