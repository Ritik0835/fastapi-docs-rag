# Keyword and dense search over the chunks produced by src.ingest.

import json
import re
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

CHUNKS_PATH = Path("data/chunks.jsonl")
EMBEDDINGS_PATH = Path("data/embeddings.npy")
IDS_PATH = Path("data/embedding_ids.json")

MODEL_NAME = "BAAI/bge-small-en-v1.5"
# Model card instruction for short queries used to find long passages.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# Load the model once and reuse it for every query.
_MODEL = None
_MODEL_NAME = None


def load_chunks(path):
    """Read a JSONL chunk file into a list of dictionaries."""
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def tokenize(text):
    """Lowercase words, keeping identifiers such as response_model intact."""
    # No stemming: identifiers and exact API names must survive.
    return re.findall(r"[a-z0-9_]+", text.lower())


def bm25_index(chunks):
    """Build a BM25 index plus the chunk IDs in index order."""
    corpus = [tokenize(chunk["text"]) for chunk in chunks]
    return {
        "bm25": BM25Okapi(corpus),
        "ids": [chunk["chunk_id"] for chunk in chunks],
    }


def bm25_search(query, index, k):
    """Return the top k chunk IDs for a keyword query."""
    scores = index["bm25"].get_scores(tokenize(query))
    # Stable sort keeps ties in the original chunk order.
    order = np.argsort(-scores, kind="stable")[:k]
    return [index["ids"][position] for position in order]


def get_model(model_name=MODEL_NAME):
    """Return a cached CPU SentenceTransformer, creating it only when needed."""
    global _MODEL, _MODEL_NAME
    if _MODEL is None or _MODEL_NAME != model_name:
        _MODEL = SentenceTransformer(model_name, device="cpu")
        _MODEL_NAME = model_name
    return _MODEL


def embed_chunks(chunks, model_name=MODEL_NAME):
    """Encode all chunks, normalize them, and save vectors plus IDs."""
    model = get_model(model_name)
    texts = [chunk["text"] for chunk in chunks]
    print(f"Encoding {len(texts)} chunks with {model_name} ...")
    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    embeddings = np.asarray(embeddings, dtype=np.float32)

    EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(EMBEDDINGS_PATH, embeddings)
    IDS_PATH.write_text(
        json.dumps([chunk["chunk_id"] for chunk in chunks]),
        encoding="utf-8",
    )
    return embeddings


def load_embeddings():
    """Load the saved embedding matrix and its matching chunk IDs."""
    embeddings = np.load(EMBEDDINGS_PATH)
    ids = json.loads(IDS_PATH.read_text(encoding="utf-8"))
    return embeddings, ids


def dense_search(query, embeddings, ids, k, model):
    """Return the top k chunk IDs by cosine similarity (dot product)."""
    # Passages were embedded without a prefix; only queries get this prefix.
    query_vector = model.encode(
        QUERY_PREFIX + query,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    query_vector = np.asarray(query_vector, dtype=np.float32).reshape(-1)
    scores = np.asarray(embeddings, dtype=np.float32) @ query_vector
    order = np.argsort(-scores, kind="stable")[:k]
    return [ids[position] for position in order]


def search(query, method, k):
    """Search chunks by 'bm25' or 'dense' and return ranked chunk IDs."""
    chunks = load_chunks(CHUNKS_PATH)
    if method == "bm25":
        return bm25_search(query, bm25_index(chunks), k)
    if method == "dense":
        embeddings, ids = load_embeddings()
        return dense_search(query, embeddings, ids, k, get_model())
    raise ValueError("method must be 'bm25' or 'dense'")
