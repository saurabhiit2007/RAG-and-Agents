## 1. Overview

Embeddings are fixed-length dense vectors that encode the semantic meaning of text. In RAG, embeddings are generated for both document chunks (at index time) and user queries (at retrieval time), and similarity between those vectors determines what gets retrieved.

---

---

## 2. Dense, Sparse, and Hybrid Embeddings

### Dense Embeddings

Text is mapped into a continuous low-dimensional vector space (typically 256–4096 dimensions) using a neural encoder. Similar texts end up near each other regardless of exact word overlap.

- **Pros:** Captures paraphrases and semantic equivalence; efficient ANN search; handles natural language queries well.

- **Cons:** Weak at exact keyword matching; sensitive to domain shift; less interpretable.

- **Examples:** Sentence-BERT, E5, GTE, OpenAI text-embedding models.

---

### Sparse Embeddings

Text is represented as a high-dimensional sparse vector over a vocabulary (most dimensions are zero). Non-zero weights correspond to terms that appear in the document or query.

- **Pros:** Excellent exact-match recall for keywords, IDs, product codes; interpretable; robust for rare terms.

- **Cons:** No semantic generalisation; fails on paraphrases; vocabulary-dependent.

- **Examples:** TF-IDF, BM25, SPLADE.

---

### Hybrid Embeddings

Hybrid approaches combine both signals. Three common strategies:

- **Late fusion (RRF):** Run dense and sparse search independently, then merge ranked lists using Reciprocal Rank Fusion. Called "late" because merging happens after both retrievals complete.

- **Two-stage retrieval:** Sparse search narrows millions of documents to a few hundred candidates; a dense model re-scores that shortlist. Balances efficiency and accuracy.

- **Joint sparse-dense (SPLADE-style):** A single model produces vectors containing both semantic signals and lexical importance weights — one unified search.

---

---

## 3. Bi-Encoders vs. Cross-Encoders

This is the most important architectural distinction in embedding-based retrieval and a near-universal interview topic.

### Bi-Encoders (Dual Encoders)

Query and document are encoded **independently** into vectors. Similarity is a dot product or cosine distance. Because document embeddings are pre-computed and stored, retrieval is O(log N) with ANN indexes.

```
s(q, d) = ⟨f(q), g(d)⟩
```

- **Strengths:** Extremely fast at scale; indexable; supports millions of documents.

- **Weakness:** No cross-attention between query and document — limited relevance modelling.

- **Used for:** First-stage retrieval (recall-optimised).

---

### Cross-Encoders

Query and document are **concatenated** and passed through a transformer together. Full self-attention across both texts allows every query token to attend to every document token.

```
s(q, d) = h([q ; d])
```

- **Strengths:** Rich token-level interactions; substantially more accurate relevance scoring.

- **Weakness:** Cannot be pre-computed or indexed — one full forward pass per query-document pair. Too slow for large corpora.

- **Used for:** Second-stage reranking over a small candidate set (precision-optimised).

> **Bi-encoders maximise recall at scale. Cross-encoders maximise precision on a shortlist. Production systems use both in sequence.**

---

### Late Interaction — ColBERT

A middle ground between bi- and cross-encoders:

- Stores a vector per **token** in each document (more memory than bi-encoders).

- Uses a **MaxSim** operation at retrieval: the score for a query token is the maximum similarity across all document token vectors.

- Achieves near cross-encoder accuracy at bi-encoder speed.

---

---

## 4. Embedding Training Objectives

### Contrastive Learning (InfoNCE / MNR Loss)

Positive pairs (query + relevant document) are pulled closer in vector space; negative examples (other documents in the batch) are pushed apart.

**InfoNCE Loss:**

```
L = -log [ exp(sim(q, d+)) / (exp(sim(q, d+)) + Σ exp(sim(q, d-))) ]
```

- **Temperature τ:** Scales similarity scores before softmax. Low τ → model focuses heavily on hardest negatives. High τ → smooths the distribution.

**Multiple Negatives Ranking (MNR) Loss:** The standard in Sentence-Transformers. In a batch of K pairs, each document serves as a negative for all other queries in the batch — providing K–1 negatives per query "for free" without manual labelling.

---

### Supervised Retrieval Fine-tuning

Models are fine-tuned on human-labelled query-document relevance datasets.

- **MS MARCO:** The gold standard — real Bing queries paired with human-judged relevant passages. Most production embedding models (BGE, GTE, E5) are trained on MS MARCO.

- **Pairwise loss:** Model is given (q, d+, d-) and penalised if d- scores higher than d+.

- **Listwise loss:** Model optimises the entire ranked list at once. More accurate for ranking (directly optimises nDCG) but more expensive to train.

---

### Matryoshka Representation Learning (MRL)

Training embeds information hierarchically so the first N dimensions contain the most important features. This enables **vector truncation** — you can store 1536-dimensional vectors but query only the first 256 dimensions to save storage and compute with minimal accuracy loss.

---

### Instruction-Tuned Embeddings

Models like Instructor and BGE accept a natural-language task prefix:

> "Represent this query for retrieving legal documents"

This lets a single model adapt its embedding space to different tasks — retrieval vs. clustering vs. classification — without separate models.

---

---

## 5. Domain Adaptation (The "Cold Start" Problem)

Generic embeddings underperform on specialist domains (medical, legal, code). Adaptation options in increasing cost order:

1. **Continued pre-training:** Run Masked Language Modeling (MLM) on your private corpus to teach the model domain vocabulary.

2. **Contrastive fine-tuning:** Use domain-specific query-document pairs with contrastive loss to pull relevant items closer.

3. **Generative Pseudo-Labeling (GPL):** Use an LLM to generate synthetic questions for each unlabeled document, then train the embedding model on these synthetic pairs. Effective with zero labeled data.

4. **Adapter-based tuning:** Insert lightweight adapter layers and fine-tune only those, leaving base model weights frozen.

> **Critical:** If you change the embedding model, you must re-index the entire corpus. Vectors from different models are not comparable.

---

---

## 6. Distance Metrics

| Metric | What It Measures | Note |
|---|---|---|
| Cosine similarity | Angle between vectors (ignores magnitude) | Most common for text; equivalent to dot product on L2-normalised vectors |
| Dot product | Projection of one vector onto another | Faster; rewards both direction and magnitude |
| Euclidean distance | Straight-line distance in vector space | Sensitive to vector magnitude; less common for text |

**Note:** Cosine similarity with L2-normalised vectors is equivalent to dot product. L2 normalisation stabilises similarity scores and improves ANN search behaviour by projecting all vectors onto a unit hypersphere.

---

---

## 7. Common Failure Modes

| Failure Mode | Root Cause | Mitigation |
|---|---|---|
| Semantic drift | Retrieved chunks are topically related but not relevant | Add cross-encoder reranker |
| Out-of-vocabulary | Search for product IDs or rare part numbers fails | Add hybrid search (BM25 or SPLADE) |
| Intent mismatch | Procedural query retrieves descriptive content | Use HyDE (hypothetical document embeddings) |
| Domain mismatch | Generic model underperforms on specialist text | Fine-tune or domain-adapt the embedding model |
| Lost in the middle | LLM ignores context deep in the prompt | Parent-Document Retrieval; reorder chunks |

---

---

## 8. Evaluation of Embeddings

**Offline (retrieval-level):**

- Recall@k — is the relevant document in the top k?

- MRR — how early does the first relevant document appear?

- nDCG — quality of the full ranked list using graded relevance.

**End-to-end:**

- Answer correctness, faithfulness, latency, and cost.

> Better retrieval does not always lead to better generation without proper prompting and context selection.

---

---

## 9. Interview Questions

**Q: Why can't you use an LLM directly for retrieval over millions of documents?**

A: Two reasons: (1) LLMs have a fixed context window and cannot "read" millions of documents in one pass; (2) attention is O(N²) in sequence length, making it computationally infeasible. Embeddings provide O(log N) search via ANN indexes.

---

**Q: What is HyDE and when would you use it?**

A: Hypothetical Document Embeddings — use an LLM to generate a "fake" ideal answer to the query, embed that answer, and retrieve real documents similar to it. This bridges the vocabulary gap between a short query and longer document text. Use it when standard retrieval misses relevant documents because the query uses different wording than the documents. Risk: if the LLM hallucinates, the hallucinated text is embedded and may retrieve wrong documents.

---

**Q: When do dense embeddings outperform BM25, and when does BM25 win?**

A: Dense embeddings win on semantic search, paraphrase matching, and natural language queries where exact document wording differs from the query. BM25 wins when queries contain rare terms, product codes, identifiers, or exact strings where lexical matching is what matters. Hybrid systems combine both to cover both failure modes.

---

**Q: Does increasing embedding dimensionality always improve performance?**

A: No. Higher dimensions increase memory, index size, and ANN search latency. Beyond a point, the "curse of dimensionality" makes distance metrics less meaningful. MRL allows trading off dimensionality versus accuracy dynamically at query time.

---

**Q: When should you re-index your vector database?**

A: Whenever you change the embedding model — you cannot compare vectors generated by Model A with those from Model B. Also re-index when the corpus changes significantly, when chunk size or preprocessing changes, or when switching to an index type that requires a full rebuild (like IVF).

---

**Q: How do bi-encoders and cross-encoders differ in how they handle relevance?**

A: Bi-encoders encode query and document independently so they cannot model interaction between the two at encoding time — they rely on global semantic similarity. Cross-encoders concatenate query and document and process them jointly, so every token in the query can attend to every token in the document. This produces much richer relevance signals but cannot be pre-computed, making it unsuitable for large-scale first-stage retrieval.

---