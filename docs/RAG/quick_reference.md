## 1. When to Use Each Retrieval Method

| Method | Use When |
|---|---|
| BM25 | Exact keyword matches matter; no training budget; queries contain IDs, codes, or rare terms; strong baseline |
| TF-IDF | Very simple baseline; interpretability is critical; no BM25 available |
| SPLADE | Want BM25 efficiency + semantic expansion; existing inverted-index infra; diverse query vocabulary |
| Dense bi-encoder | Natural language queries; paraphrase matching; fine-grained semantic similarity |
| Hybrid (dense + sparse) | Production systems; diverse query types; best overall recall and precision |
| Cross-encoder (reranker) | Second-stage precision boost over 50–100 candidates; latency is acceptable |

---

---

## 2. Chunking Strategy Decision Guide

| Document Type | Recommended Strategy |
|---|---|
| Uniform text (articles, reports) | Sentence-based or paragraph-based |
| Structured docs with headings (PDFs, wikis) | Recursive chunking |
| Long documents, multi-hop queries | Sliding window or recursive |
| High-precision, smaller corpus | Semantic/context-aware |
| Tables | Row-based with schema metadata |
| Source code | Function-level or class-level |

---

---

## 3. Chunk Size and Top-k Reference

| Chunk Size | Top-k (retrieval) | Top-m (after reranker) | Tradeoff |
|---|---|---|---|
| Small (100–300 tokens) | 20–50 | 5–10 | High recall, more context noise |
| Medium (300–700 tokens) | 10–20 | 5–10 | Balanced — good default |
| Large (700–1500 tokens) | 3–8 | 3–5 | High precision, risk of missing info |

---

---

## 4. Retrieval Failure Diagnostic Flow

```
Low answer quality?
  │
  ├─ Check Recall@k
  │     Is the relevant document in top-k?
  │     NO → Fix the retriever:
  │           - Better embedding model
  │           - Add hybrid search (BM25 + dense)
  │           - Add query expansion or HyDE
  │           - Adjust chunk size
  │           - Add metadata filters
  │
  ├─ Check Context Precision
  │     Are the retrieved documents actually relevant?
  │     NO → Add cross-encoder reranker
  │           Improve chunking to reduce noise
  │
  ├─ Check Faithfulness
  │     Is the answer grounded in retrieved text?
  │     NO → Improve prompt (citation constraints)
  │           Add explicit grounding instructions
  │           Check for context window overflow
  │
  └─ Check Answer Correctness
        Is the grounded answer actually right?
        NO → Retrieved documents may be wrong, outdated, or insufficient
              Update corpus; validate sources; improve coverage
```

---

---

## 5. Key Parameter Defaults

| Parameter | Default / Starting Point | Notes |
|---|---|---|
| Chunk size | 400–600 tokens | Tune based on query type and embedding model |
| Chunk overlap | 10–15% of chunk size | Mitigates boundary loss; increases index size |
| Top-k (first-stage retriever) | 50–100 | Higher for hybrid; lower in resource-constrained systems |
| Top-m (after reranker) | 5–10 | What the LLM actually sees |
| BM25 k₁ | 1.5 | Controls TF saturation speed |
| BM25 b | 0.75 | Controls length normalisation strength |
| RRF constant k | 60 | Robustly combines ranked lists; rarely needs tuning |
| HNSW M | 16–64 | Higher = better recall, more memory |
| HNSW ef_search | 100–200 | Higher = better recall, slower queries |

---

---

## 6. Architecture Decision Matrix

| System Size | Latency Req. | Update Freq. | Recommended Architecture |
|---|---|---|---|
| Small (<100k docs) | Any | Any | Flat index or HNSW + BM25 hybrid |
| Medium (100k–10M docs) | Low | Frequent | HNSW + sparse, with cross-encoder reranker |
| Large (>10M docs) | Low | Infrequent | IVF+PQ + sparse, with reranker |
| Very large (>1B docs) | Very low | Infrequent | IVF+PQ, distributed (Milvus), managed (Pinecone) |

---

---

## 7. Bi-Encoder vs. Cross-Encoder Quick Reference

| | Bi-Encoder | Cross-Encoder |
|---|---|---|
| Encoding | Query and doc separately | Query + doc concatenated together |
| Pre-computation | Doc embeddings stored at index time | Must run at query time per candidate |
| Scalability | Millions of docs | ~50–100 candidates |
| Recall / Precision | High recall | High precision |
| Speed | Very fast (ANN search) | Slow (full forward pass per pair) |
| Used in | First-stage retrieval | Reranking |

---

---

## 8. Evaluation Metric Summary

| Metric | Stage | What It Measures |
|---|---|---|
| Recall@k | Retrieval | Is relevant doc in top k? |
| MRR | Retrieval | How early is first relevant doc? |
| nDCG | Retrieval | Full ranked list quality (graded relevance) |
| Precision@k | Retrieval | What fraction of top-k is relevant? |
| Exact Match (EM) | Generation | Exact string match with reference |
| F1 (token) | Generation | Token overlap with reference |
| BERTScore | Generation | Semantic similarity to reference |
| Faithfulness | End-to-end | Claims supported by retrieved context? |
| Answer Relevance | End-to-end | Does answer address the query? |
| Context Precision | End-to-end | Are retrieved docs relevant? |
| Context Recall | End-to-end | Does context contain required info? |

---

---

## 9. The Production RAG Checklist

- [ ] Define evaluation metrics before building (Recall@k, faithfulness, answer correctness).

- [ ] Choose chunk size and strategy; evaluate retrieval recall before touching the LLM.

- [ ] Start with hybrid retrieval (BM25 + dense) as the first-stage retriever.

- [ ] Add a cross-encoder reranker; measure Precision@5 improvement.

- [ ] Attach metadata to all chunks; implement filtered retrieval.

- [ ] Implement faithfulness and groundedness checks before shipping.

- [ ] Run the oracle experiment to confirm failures are in retrieval, not generation.

- [ ] Log queries, retrieved context, and answers in production for continuous evaluation.

- [ ] Re-index when changing embedding models.

- [ ] Build a held-out evaluation set; validate LLM-as-a-judge scores against humans.

---

---

## 10. Top Interview Topics by Frequency

| Topic | Frequency | Key Point to Know |
|---|---|---|
| RAG vs. fine-tuning | Very high | RAG = knowledge access; fine-tuning = behaviour change |
| Bi-encoder vs. cross-encoder | Very high | Bi = fast/recall; cross = slow/precision; use both in sequence |
| Chunking strategy choice | High | Recursive is the production default; tune size + top-k jointly |
| BM25 vs. dense retrieval | High | Complementary; BM25 = exact match; dense = semantics |
| Hybrid retrieval + RRF | High | Best overall quality; RRF is robust without weight tuning |
| Faithfulness vs. correctness | High | Faithfulness = grounded in context; correctness = matches truth |
| HyDE | Medium | Embed hypothetical answer instead of query to bridge vocab gap |
| Lost in the middle | Medium | LLMs miss context in the middle; put best docs first/last |
| HNSW vs. IVF | Medium | HNSW = recall/speed; IVF = memory efficiency |
| RAGAS / LLM-as-judge | Medium | Standard eval framework; validate against human labels |

---
