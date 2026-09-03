import re

from langdetect import detect, LangDetectException

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


# Load English stopwords
STOP_WORDS = set(stopwords.words("english"))


def clean_text(text):
    """
    Clean complaint text for NLP processing.
    """

    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r"http\S+|www\S+", "", text)

    # Remove special characters
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


def detect_language(text):
    """
    Detect the language of the complaint.
    """

    if not text:
        return "unknown"

    try:
        return detect(text)

    except LangDetectException:
        return "unknown"


def extract_keywords(text):
    """
    Extract meaningful words from complaint text.
    """

    cleaned = clean_text(text)

    if not cleaned:
        return []

    tokens = word_tokenize(cleaned)

    keywords = []

    for token in tokens:

        if token not in STOP_WORDS and token.isalpha():

            if len(token) > 2:
                keywords.append(token)

    # Remove duplicates while preserving order
    keywords = list(dict.fromkeys(keywords))

    return keywords


def analyze_complaint(text):
    """
    Main NLP analysis function.
    """

    language = detect_language(text)

    cleaned_text = clean_text(text)

    keywords = extract_keywords(text)

    return {
        "language": language,
        "cleaned_text": cleaned_text,
        "keywords": keywords
    }