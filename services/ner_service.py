


# Load pre-trained BERT NER model
from transformers import pipeline

ner_pipeline = None

def get_ner_pipeline():
    global ner_pipeline

    if ner_pipeline is None:
        ner_pipeline = pipeline(
            "ner",
            model="dslim/bert-base-NER",
            aggregation_strategy="simple"
        )

    return ner_pipeline


def extract_entities(text):
    """
    Extract named entities from complaint text.
    """

    if not text:
        return []

    results = get_ner_pipeline()(text)

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