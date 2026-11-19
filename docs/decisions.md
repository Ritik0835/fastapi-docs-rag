# Decision log

## 1. Corpus

- Decision: Use the English FastAPI documentation from `https://github.com/fastapi/fastapi`, folder `docs/en/docs`, copied unchanged to `data/raw/`. Source commit: `05e6df7e906c3decba377c37548019973f40bf15`.
- Alternatives rejected: Translated docs folders (`docs/de/docs`, `docs/es/docs`, etc.), scraping the live website, and using API reference only.
- Reason: The user asked for English docs; the Markdown source is stable, versioned, and easy to cite by file path.
- Date: 2026-11-19

## 2. Keyword search

- Decision: Use `rank-bm25` for lexical/BM25 retrieval.
- Alternatives rejected: Elasticsearch/OpenSearch (extra server), Whoosh (another index to maintain), and a hand-written TF-IDF scorer (more code for no clear gain).
- Reason: `rank-bm25` is small, pure Python, CPU-friendly, and works well on a small corpus.
- Date: 2026-11-19

## 3. Embeddings

- Decision: Use `BAAI/bge-small-en-v1.5` for dense embeddings. The query prefix was checked on the model card at `https://huggingface.co/BAAI/bge-small-en-v1.5`: the card lists `Represent this sentence for searching relevant passages: ` as the query instruction for retrieval, adds it to queries for short-query-to-long-passage search, and says passages get no instruction. Phase 1 must confirm the prefix choice when the model is actually used.
- Alternatives rejected: `sentence-transformers/all-MiniLM-L6-v2` (lower retrieval score on the card), `BAAI/bge-base-en-v1.5` and `BAAI/bge-large-en-v1.5` (larger and slower on CPU), and hosted embedding APIs (extra cost and a key).
- Reason: Small English model with strong benchmark results and 384-dimensional vectors, which keeps CPU indexing cheap. No model weights were downloaded in Phase 0.
- Date: 2026-11-19

## 4. Reranker

- Decision: Use `cross-encoder/ms-marco-MiniLM-L-6-v2` to rerank candidates.
- Alternatives rejected: `BAAI/bge-reranker-base` (heavier on CPU), reranking with the embedding model, and no reranking stage.
- Reason: Small cross-encoder that can rescore a short candidate list on CPU without a GPU. No model weights were downloaded in Phase 0.
- Date: 2026-11-19

## 5. Vector store

- Decision: Keep dense vectors in a NumPy array saved to disk.
- Alternatives rejected: A vector database server (for example Qdrant or Milvus), because the corpus is small; a SQLite extension, because it adds setup without a benefit here.
- Reason: A single `.npy` file is simple, fast enough for this corpus, easy to inspect, and needs no extra service.
- Date: 2026-11-19

## 6. Generator and judge (OPEN)

- Decision: OPEN. Candidates: Groq for the answer generator, and a different provider such as Gemini or Mistral for the independent judge, so the same vendor does not grade its own output. The final choice and its rate limits will be recorded in Phase 2.
- Alternatives rejected: None finally rejected yet; using the same provider for both roles is currently disfavoured.
- Reason: Keep the generator and judge independent while avoiding premature provider lock-in. No API keys are stored in this repository.
- Date: 2026-11-19

## 7. Experiment tracking

- Decision: Use MLflow to log retrieval ablation runs.
- Alternatives rejected: Hand-written CSV/JSON logs (no comparison UI), Weights & Biases (external account and network dependency).
- Reason: MLflow runs locally, records parameters and metrics, and is already installed for this project.
- Date: 2026-11-19

## 8. Deployment

- Decision: Deploy on Render using Docker.
- Alternatives rejected: Serverless platforms such as Vercel (less suitable for a long-running Python service), and a manually managed VM (more ops work).
- Reason: Render can build and run a Docker image directly, which keeps deployment reproducible and matches the Docker image planned for Phase 8.
- Date: 2026-11-19
