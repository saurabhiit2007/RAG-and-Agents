## 1. Overview

Reranking is a second-stage step that re-scores a small candidate set returned by the first-stage retriever. The goal is to shift from recall-optimised to precision-optimised — ensuring the documents that actually enter the LLM prompt are the most relevant, not just the most similar embeddings.

---

---

## 2. Why Reranking Is Necessary

First-stage retrievers (bi-encoders, BM25) are optimised for speed and recall. They encode query and document independently, which means they cannot model fine-grained relevance — the nuanced relationship between a specific question and a specific passage. A document that is semantically similar to a query may not actually answer it.

**Example:** The query "What are the side effects of aspirin in elderly patients?" will semantically match many documents about aspirin. A bi-encoder may rank a general "aspirin overview" above a document that specifically discusses geriatric dosing risks — because the general document has higher semantic overlap. A cross-encoder reranker, reading both query and document together, would correctly identify the more specific document as more relevant.

Rerankers fix this by evaluating each candidate in full context of the query.

---

---

## 3. Cross-Encoder Reranking

The standard reranking approach. The query and each candidate document are concatenated and fed through a transformer together. Full self-attention across both texts allows every query token to attend to every document token.

**How it works:**

1. First-stage retriever returns top-k candidates (typically 50–100).

2. For each candidate, concatenate `[CLS] query [SEP] document [SEP]` and run through the cross-encoder.

3. The model outputs a single relevance score per candidate.

4. Re-sort candidates by these scores; pass top-m (typically 5–10) to the LLM.

| | |
|---|---|
| **Pros** | Substantially higher precision than bi-encoders; captures exact question-answer relevance; rich token-level interactions |
| **Cons** | Cannot be pre-computed or indexed; one full forward pass per candidate — O(k) per query; too slow for first-stage retrieval on large corpora |

---

---

## 4. The Two-Stage Recall → Precision Pipeline

The canonical production pattern combines a fast first-stage retriever with a slower but accurate reranker:

```
Query
  │
  ▼
Stage 1: First-stage retriever (bi-encoder or BM25)
         → Retrieve top 50–100 candidates
         → Fast, recall-optimised (O(log N) search)
  │
  ▼
Stage 2: Reranker (cross-encoder)
         → Re-score all 50–100 candidates
         → Slow, precision-optimised (O(k) forward passes)
         → Return top 5–10
  │
  ▼
Stage 3: LLM generation
         → Receives only top 5–10 reranked documents as context
```

> Adding a cross-encoder reranker is one of the highest-ROI improvements in a RAG system. The first retriever casts a wide net; the reranker ensures only the most relevant content reaches the LLM.

---

---

## 5 LLM-Based Reranking

An LLM is prompted to score or rank candidates rather than using a dedicated cross-encoder.

**Strategies:**

- **Pointwise:** Score each document independently on a scale (e.g., 0–10 relevance).

- **Pairwise:** Compare two documents at a time and identify the more relevant one.

- **Listwise:** Ask the LLM to sort the entire candidate list and return the ranked order.

| | |
|---|---|
| **Pros** | Flexible — can use task-specific instructions; can reason about relevance semantically |
| **Cons** | Most expensive (LLM API cost per reranking); non-deterministic; prompt-sensitive |

**When to use:** When cross-encoder models underperform on your domain; when you need explainable relevance reasoning; when latency constraints are loose.

---

---

## 6. Reranker Models

| Model | Notes |
|---|---|
| `ms-marco-MiniLM-L-6-v2` | Fast, small cross-encoder fine-tuned on MS MARCO — good default |
| `bge-reranker-large` | Strong performance; part of the BGE family |
| `cross-encoder/ms-marco-electra-base` | Stronger than MiniLM, still fast |
| Cohere Rerank API | Managed API; good multilingual support |
| GPT-4 / Claude (listwise) | Most accurate but highest latency and cost |

---

---

## 7. Reranking in Hybrid Systems

In hybrid retrieval pipelines (dense + sparse), reranking typically happens after Reciprocal Rank Fusion merges the two result sets:

```
Dense retrieval → top 100
                        ↘
                         RRF merge → top 100 fused → Cross-encoder reranker → top 10 → LLM
                        ↗
Sparse retrieval → top 100
```

This architecture maximises both recall (hybrid retrieval) and precision (cross-encoder reranking).

---

---

## 8. Interview Questions

**Q: Why use a bi-encoder for retrieval instead of a cross-encoder from the start?**

A: Cross-encoders cannot be pre-computed — every query-document pair requires a full model pass, so you cannot index documents ahead of time. A bi-encoder pre-computes all document embeddings once and stores them. At query time you only encode the query once and find nearest neighbours with fast math. For a corpus of 1 million documents, a cross-encoder would require 1 million forward passes per query — completely infeasible. Bi-encoders make retrieval tractable; cross-encoders then improve precision on a small shortlist.

---

**Q: What is a good top-k for the first-stage retriever?**

A: Typically 50–100. Large enough to have high recall (not miss relevant documents), small enough to keep reranking latency manageable. The exact number depends on the reranker's latency budget and how many documents will ultimately be passed to the LLM (usually 5–10). In hybrid systems, each retriever returns 50–100 and RRF merges them before reranking.

---

**Q: What happens if the first-stage retriever misses the relevant document entirely?**

A: The reranker cannot help — it can only reorder what was already retrieved. This is why first-stage recall is so critical. If Recall@100 is low, invest in improving the retriever (better embedding model, hybrid retrieval, query expansion) rather than in a better reranker. The reranker is a precision tool, not a recall tool.

---

**Q: How do you evaluate whether a reranker is actually helping?**

A: Compare Precision@5 (or Precision@10) before and after reranking on a labelled evaluation set. Also measure MRR — whether the most relevant document is moving to a higher rank. End-to-end, measure faithfulness and answer correctness before/after adding the reranker. Watch latency as a cost: cross-encoder reranking adds 50–200ms per query depending on model size and number of candidates.

---

**Q: What is the difference between reranking and retrieval?**

A: Retrieval selects candidates from the full corpus — it must be fast and prioritises recall. Reranking re-scores a small shortlist — it can be slower and prioritises precision. Retrieval uses approximate methods (ANN, BM25) that scale to millions of documents. Reranking uses exact, expensive methods (cross-encoders, LLMs) that only work on tens to hundreds of candidates. They serve complementary roles in the pipeline.

---