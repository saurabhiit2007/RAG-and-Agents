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

**Discriminative cross-encoders** (standard approach):

| Model | Notes |
|---|---|
| `ms-marco-MiniLM-L-6-v2` | Fast, small — good default for latency-sensitive systems |
| `bge-reranker-v2-m3` | Strong multilingual cross-encoder from BAAI |
| `cross-encoder/ms-marco-electra-base` | Higher accuracy than MiniLM, still fast |
| Cohere Rerank v3 | Managed API; strong multilingual support |

**Generative rerankers** (2023–2024):

| Model | Approach | Notes |
|---|---|---|
| **MonoT5** (Nogueira et al., 2020) | T5 generates "true"/"false" for each (query, doc) pair | Strong baseline for generative reranking |
| **RankZephyr** (2024) | Zephyr-7B fine-tuned for listwise ranking | Strong open-source listwise reranker |
| **RankGPT** | GPT-4 prompted for sliding window listwise ranking | Highest quality; high latency and cost |

> **Discriminative vs. generative rerankers:** Discriminative models (cross-encoders) produce a relevance score directly. Generative models produce text ("true"/"false" or a ranked list) and are more flexible but slower. For most RAG applications, a discriminative cross-encoder is the right default.

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
