# Tests for keyword and dense search over the saved chunks.

from pathlib import Path

from src.retrieval import (
    CHUNKS_PATH,
    bm25_index,
    bm25_search,
    dense_search,
    get_model,
    load_chunks,
    load_embeddings,
)


def test_bm25_results_are_known_chunk_ids():
    chunks = load_chunks(CHUNKS_PATH)
    known_ids = {chunk["chunk_id"] for chunk in chunks}
    results = bm25_search("how do I declare an optional query parameter", bm25_index(chunks), 5)
    assert results
    assert all(chunk_id in known_ids for chunk_id in results)


def test_identifier_query_response_model():
    chunks = load_chunks(CHUNKS_PATH)
    by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
    results = bm25_search("response_model", bm25_index(chunks), 5)
    assert any("response_model" in by_id[chunk_id]["text"] for chunk_id in results)


def test_dense_search_returns_k_existing_ids():
    chunks = load_chunks(CHUNKS_PATH)
    known_ids = {chunk["chunk_id"] for chunk in chunks}
    embeddings, ids = load_embeddings()
    results = dense_search("CORS middleware", embeddings, ids, 3, get_model())
    assert len(results) == 3
    assert all(chunk_id in known_ids for chunk_id in results)
