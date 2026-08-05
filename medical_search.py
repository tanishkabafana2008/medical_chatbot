"""
Semantic (RAG-style) search over the medical dataset.

This is optional: if medical_embeddings.pkl hasn't been generated yet
(run `python medical_embeddings.py` to create it), search_medical_data()
just returns None and the chatbot falls back to plain keyword lookup
instead of crashing the whole app on import.
"""

import os
import pickle

_model = None
_documents = None
_embeddings = None
_load_attempted = False


def _load():
    global _model, _documents, _embeddings, _load_attempted

    if _load_attempted:
        return
    _load_attempted = True

    if not os.path.exists("medical_embeddings.pkl"):
        return

    try:
        from sentence_transformers import SentenceTransformer

        with open("medical_embeddings.pkl", "rb") as file:
            data = pickle.load(file)

        _documents = data["documents"]
        _embeddings = data["embeddings"]
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
        print(f"Could not load semantic search index: {e}")
        _model = None
        _documents = None
        _embeddings = None


def search_medical_data(question, min_confidence=0.35):
    _load()

    if _model is None or _documents is None:
        return None

    from sklearn.metrics.pairwise import cosine_similarity

    question_embedding = _model.encode([question])
    scores = cosine_similarity(question_embedding, _embeddings)[0]

    best_index = scores.argmax()
    confidence = scores[best_index]

    if confidence < min_confidence:
        return None

    return _documents[best_index]
