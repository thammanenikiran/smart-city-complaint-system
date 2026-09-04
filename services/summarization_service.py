"""
Summarization Service

Uses FLAN-T5 to generate concise summaries of complaint descriptions.
"""

from transformers import T5Tokenizer, T5ForConditionalGeneration


_tokenizer = None
_model = None
SUMMARIZER_LOADED = False


def get_summarizer():
    global _tokenizer, _model, SUMMARIZER_LOADED

    if not SUMMARIZER_LOADED:
        try:
            _tokenizer = T5Tokenizer.from_pretrained(
                "google/flan-t5-small"
            )

            _model = T5ForConditionalGeneration.from_pretrained(
                "google/flan-t5-small"
            )

            SUMMARIZER_LOADED = True

        except Exception as e:
            print(f"[WARNING] Summarization model failed to load: {e}")
            SUMMARIZER_LOADED = False

    return _tokenizer, _model


def summarize_complaint(text):
    """
    Generate a concise summary of a complaint description.
    """

    if not text or len(text.strip()) < 20:
        return text.strip() if text else ""

    tokenizer, model = get_summarizer()

    if model is None or tokenizer is None:
        return text[:100].strip() + "..." if len(text) > 100 else text

    try:
        input_text = (
            f"Summarize this civic complaint in one sentence: {text}"
        )

        if len(input_text) > 512:
            input_text = input_text[:512]

        input_ids = tokenizer(
            input_text,
            return_tensors="pt",
            max_length=512,
            truncation=True
        ).input_ids

        outputs = model.generate(
            input_ids,
            max_new_tokens=60,
            num_beams=2,
            early_stopping=True
        )

        summary = tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )

        return summary.strip() if summary else text[:100]

    except Exception as e:
        print(f"[WARNING] Summarization failed: {e}")
        return text[:100].strip() + "..." if len(text) > 100 else text