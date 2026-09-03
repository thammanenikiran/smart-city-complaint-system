from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# Load sentence embedding model
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def calculate_similarity(text1, text2):
    """
    Calculate semantic similarity between two complaints.
    """

    if not text1 or not text2:
        return 0.0

    embeddings = embedding_model.encode(
        [text1, text2]
    )

    similarity = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]]
    )[0][0]

    return round(
        float(similarity) * 100,
        2
    )


def is_duplicate(similarity_score):
    """
    Determine whether two complaints are
    sufficiently similar to be considered duplicates.
    """

    return similarity_score >= 85