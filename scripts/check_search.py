# Manual top-3 search check for the ten Phase 1 example queries.

import sys
from pathlib import Path

# Running this file directly puts scripts/ on sys.path, so add the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval import (
    CHUNKS_PATH,
    bm25_index,
    bm25_search,
    dense_search,
    get_model,
    load_chunks,
    load_embeddings,
)

QUERIES = [
    "how do I declare an optional query parameter",
    "path parameters with type validation",
    "response_model",
    "dependency injection with Depends",
    "background tasks after response",
    "how to upload a file",
    "CORS middleware",
    "JWT authentication OAuth2",
    "Pydantic model request body",
    "startup and shutdown events",
]
OUTPUT = Path("results/manual_check_phase1.txt")


def heading_paths(by_id, chunk_ids):
    """Turn ranked chunk IDs into readable heading paths."""
    return [by_id[chunk_id]["heading_path"] for chunk_id in chunk_ids]


def main():
    """Print and save BM25 and dense top-3 heading paths for each query."""
    chunks = load_chunks(CHUNKS_PATH)
    by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    bm25 = bm25_index(chunks)
    embeddings, ids = load_embeddings()
    model = get_model()

    lines = []
    for query in QUERIES:
        lines.append(f"Query: {query}")

        bm25_ids = bm25_search(query, bm25, 3)
        lines.append("  BM25 top 3:")
        for rank, heading in enumerate(heading_paths(by_id, bm25_ids), 1):
            lines.append(f"    {rank}. {heading}")

        dense_ids = dense_search(query, embeddings, ids, 3, model)
        lines.append("  Dense top 3:")
        for rank, heading in enumerate(heading_paths(by_id, dense_ids), 1):
            lines.append(f"    {rank}. {heading}")

        lines.append("")

    text = "\n".join(lines)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
