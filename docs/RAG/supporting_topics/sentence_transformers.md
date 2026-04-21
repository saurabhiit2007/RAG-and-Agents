# Sentence Transformers

Sentence Transformers (bi-encoders) are covered fully in [Embedding](../embedding.md) — sections on dense embeddings, bi-encoders vs cross-encoders, training objectives (MNR loss, contrastive learning), domain adaptation, and evaluation.

Key points for quick recall:

- Encode query and document **independently** → dot product for similarity
- Embeddings are **pre-computed** and stored in a vector index (ANN search)
- Trained with **Multiple Negatives Ranking (MNR) loss** — other documents in the batch serve as negatives for free
- Strong at semantic similarity; weak at exact keyword matching
- Use alongside BM25/SPLADE in hybrid retrieval to cover both failure modes
