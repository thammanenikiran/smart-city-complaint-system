"""
Summarization Service

Uses FLAN-T5 to generate concise and relevant summaries
of civic complaint descriptions.
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

            print("[INFO] Summarization model loaded successfully.")

        except Exception as e:
            print(f"[WARNING] Summarization model failed to load: {e}")
            SUMMARIZER_LOADED = False

    return _tokenizer, _model


def summarize_complaint(text):
    """
    Generate a concise, relevant summary of a civic complaint.

    The summary should:
    - describe the main civic problem
    - mention important secondary problems
    - mention the major impact/risk
    - remain concise
    """

    if not text:
        return ""

    text = text.strip()

    if len(text) < 40:
        return text

    tokenizer, model = get_summarizer()

    # Fallback if model cannot be loaded
    if model is None or tokenizer is None:
        return _fallback_summary(text)

    try:
        # FLAN-T5 works better when given a clear task instruction.
        input_text = (
            "Summarize the following civic complaint in one clear sentence. "
            "Keep the main problem, important secondary issue, and major impact. "
            "Do not add information that is not present in the complaint. "
            "Civic complaint: "
            + text
        )

        # Tokenize using tokens rather than Python characters.
        inputs = tokenizer(
            input_text,
            return_tensors="pt",
            max_length=512,
            truncation=True
        )

        outputs = model.generate(
            inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_new_tokens=50,
            min_new_tokens=15,
            num_beams=4,
            no_repeat_ngram_size=3,
            length_penalty=1.0,
            early_stopping=True
        )

        summary = tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        ).strip()

        # Validate generated output
        if not summary:
            return _fallback_summary(text)

        # Sometimes instruction-following models return the prompt
        # or an extremely short response.
        if len(summary) < 20:
            return _fallback_summary(text)

        return summary

    except Exception as e:
        print(f"[WARNING] Summarization failed: {e}")
        return _fallback_summary(text)


def _fallback_summary(text):
    """
    Safe fallback when the AI summarizer is unavailable.

    Uses the first complete sentence instead of blindly
    cutting the complaint at 100 characters.
    """

    sentences = text.replace("\n", " ").split(".")

    for sentence in sentences:
        sentence = sentence.strip()

        if len(sentence) >= 30:
            return sentence + "."

    if len(text) > 150:
        return text[:150].rsplit(" ", 1)[0] + "..."

    return text