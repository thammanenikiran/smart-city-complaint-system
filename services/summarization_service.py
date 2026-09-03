"""
Summarization Service

Uses FLAN-T5 to generate concise summaries of complaint descriptions.
Uses direct model inference since T5 is a seq2seq (encoder-decoder) model.
"""

from transformers import T5Tokenizer, T5ForConditionalGeneration


# Load summarization model directly (FLAN-T5 small)
try:
    _tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-small")
    _model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-small")
    SUMMARIZER_LOADED = True

except Exception as e:
    print(f"[WARNING] Summarization model failed to load: {e}")
    SUMMARIZER_LOADED = False
    _tokenizer = None
    _model = None


def summarize_complaint(text):
    """
    Generate a concise summary of a complaint description.

    Input: Long complaint text
    Output: Concise summary string

    Uses FLAN-T5 for abstractive summarization via direct inference.
    Falls back to text truncation if model unavailable.
    """

    if not text or len(text.strip()) < 20:
        return text.strip() if text else ""

    if not SUMMARIZER_LOADED or _model is None:
        # Fallback: return first 100 characters
        return text[:100].strip() + "..." if len(text) > 100 else text

    try:
        # Prepare input with summarization instruction
        input_text = (
            f"Summarize this civic complaint in one sentence: {text}"
        )

        # Truncate very long inputs to avoid model limits
        if len(input_text) > 512:
            input_text = input_text[:512]

        # Tokenize
        input_ids = _tokenizer(
            input_text,
            return_tensors="pt",
            max_length=512,
            truncation=True
        ).input_ids

        # Generate summary
        outputs = _model.generate(
            input_ids,
            max_new_tokens=60,
            num_beams=2,
            early_stopping=True
        )

        # Decode
        summary = _tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )

        return summary.strip() if summary else text[:100]

    except Exception as e:
        print(f"[WARNING] Summarization failed: {e}")
        return text[:100].strip() + "..." if len(text) > 100 else text
