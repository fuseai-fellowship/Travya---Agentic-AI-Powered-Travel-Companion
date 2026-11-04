# 0002. Use pgvector for guide retrieval instead of FAISS

- Status: accepted
- Date: 2026-11-04

## Context

The planner and the assistant need relevant passages from destination guides (retrieval-augmented
generation). The prototype kept a FAISS index in process memory and computed embeddings locally with
PyTorch models. That put a heavy ML runtime into the API image, lost the index on every restart,
could not be shared between instances, and in places queried with random vectors. The target host is a free-tier
Cloud Run instance with 512 MiB of memory that scales to zero.

## Decision

Store guide chunks and their embeddings in Postgres with pgvector (`knowledge_chunks`,
`backend/app/models/content.py`):

- 768-dimensional Gemini embeddings (`gemini-embedding-2`, truncated and re-normalised), with
  `RETRIEVAL_DOCUMENT` for chunks and `RETRIEVAL_QUERY` for questions;
- an HNSW index with cosine distance;
- lazy indexing: the first plan or question for a destination fetches its Wikivoyage guide, chunks it
  (about 900 characters, at most 60 chunks) and stores it; later requests only query;
- every chunk keeps its source URL and licence;
- deterministic hash embeddings in offline mode, so tests use the same tables and queries.

## Consequences

- One datastore for application data and vectors: transactional, backed up together, available on
  Neon's free plan.
- The API image carries no ML runtime, so it stays small and starts fast enough to scale from zero.
- The index is shared by all instances and survives restarts; each destination is embedded once.
- The vector dimension is fixed in the schema; changing the embedding model or dimension needs a
  migration and re-embedding.
- Embedding calls use the Gemini quota; queries add one embedding request each.
- Retrieval quality depends on Wikivoyage's coverage; destinations without a guide fall back to a
  Wikipedia summary or to no guide at all.

## Alternatives considered

- **FAISS in process**: fast, but memory-bound, lost on restart, not shared, and it pulls in a heavy
  native stack.
- **A hosted vector database** (Pinecone, Vertex AI Vector Search): another account, network hop and
  bill, for a corpus of a few thousand chunks.
- **Chroma or another embedded store**: same persistence and sharing problems as FAISS on a stateless
  host.
- **No retrieval**: the planner would rely on the model's memory of each destination, which makes
  sources impossible to cite.
