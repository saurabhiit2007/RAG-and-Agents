## 1. Overview

Indexing defines how embeddings are organised for fast similarity search at scale. The right indexing strategy depends on corpus size, latency requirements, update frequency, and memory constraints. If the retriever is the bottleneck for RAG quality, the index is what makes the retriever fast enough to use in production.

---

---

## 2. Flat Index (Exact Search)

Computes similarity against every vector in the database. Recall is perfect by definition — no approximation.

- **Pros:** Exact results; simple implementation; deterministic.

- **Cons:** Linear search time — O(N) per query; unusable in production for large corpora.

- **Use when:** Small datasets (up to ~100k vectors); offline ground-truth benchmarking; evaluating other indexes.

---

---

## 3 Approximate Nearest Neighbor (ANN) Indexes

ANN indexes trade a small accuracy loss for large performance gains. The two dominant approaches are HNSW and IVF.

### HNSW (Hierarchical Navigable Small World)

Builds a multi-layer graph where each node connects to similar vectors. Search starts at higher (coarser) layers and progressively refines through lower (finer) layers. The "navigable small world" property ensures short paths between any two nodes in the graph.

**How it works:**

- During indexing, each new vector is inserted into multiple layers, with connections to its nearest neighbours at each layer.

- During search, the algorithm enters at the top layer (fewest nodes), greedily navigates to the nearest centroid, then descends layer by layer for increasing refinement.

| | |
|---|---|
| **Pros** | Very high recall at low latency; supports dynamic insertion without full rebuild; tunable recall/speed tradeoff |
| **Cons** | High memory overhead from graph edges (typically 2–8x raw vector storage); slow build on very large datasets |
| **Best for** | Latency-sensitive RAG; medium-to-large corpora; frequently updated data |

**Key parameters:**

- `M` — number of connections per node. Higher M → better recall, more memory.

- `ef_construction` — search width during index build. Higher → better index quality, slower build.

- `ef_search` — search width at query time. Higher → better recall, slower queries.

---

### IVF (Inverted File Index)

Clusters all vectors into `n_list` centroid clusters at build time. At query time, only the `n_probe` closest cluster centroids are searched.

**Analogy to classical inverted index:** Instead of `term → documents`, IVF uses `centroid ID → vectors assigned to that centroid`. Only vectors in the probed clusters are evaluated.

| | |
|---|---|
| **Pros** | Lower memory than HNSW; faster to build; disk-backed search feasible |
| **Cons** | Lower recall than HNSW if relevant vectors fall outside probed clusters; sensitive to clustering quality |
| **Best for** | Very large datasets; cost-constrained or memory-constrained systems |

**Key parameters:**

- `n_list` — number of clusters. More clusters → higher precision but longer build time.

- `n_probe` — number of clusters searched at query time. More probes → higher recall, slower queries.

---

### Product Quantization (PQ)

Compresses high-dimensional vectors into compact codes by splitting each vector into sub-vectors and quantising each sub-vector independently using a trained codebook.

- **Pros:** Massive memory reduction — enables storage of billions of vectors; lower I/O cost.

- **Cons:** Lossy compression — recall drops due to quantisation errors; harder to debug.

- **Typically combined with:** IVF+PQ for extreme-scale search (e.g., web-scale retrieval).

---

### ANN Index Comparison

| Index | Recall | Query Speed | Memory | Update Support | Best For |
|---|---|---|---|---|---|
| Flat (exact) | Perfect | Slow (linear) | Low | Easy | Ground truth, small datasets |
| HNSW | Very high | Very fast | High | Easy (dynamic) | Production RAG, latency-sensitive |
| IVF | High | Fast | Medium | Requires rebuild | Large scale, memory-constrained |
| IVF+PQ | Moderate | Very fast | Very low | Requires rebuild | Billion-scale search |
| Sparse (BM25) | High (lexical) | Very fast | Low | Easy | Keyword search, hybrid RAG |

---

---

## 4. Sparse Indexes

Sparse indexes use term-based inverted indexes mapping `term → posting list of documents`. Standard infrastructure for BM25 and SPLADE. Implemented in Elasticsearch, OpenSearch, and Lucene.

- **Excellent for:** Lexical retrieval; exact keyword matches; rare terms and identifiers.

- **Cannot do:** Semantic similarity; paraphrase matching.

---

---

## 5. Hybrid Indexing

Hybrid systems maintain both a dense vector index and a sparse inverted index. Retrieval runs in parallel across both, and results are merged (typically with Reciprocal Rank Fusion).

- **Pros:** Improved recall and precision; robust to diverse query types; production-proven.

- **Cons:** Increased system complexity; higher latency (two retrieval paths); requires score fusion tuning.

---

---

## 6. Vector Databases

Vector databases manage embedding storage, indexing, ANN search, metadata filtering, and scaling in a unified system. Key selection criteria: index type support, metadata filtering capabilities, update model, latency guarantees, and operational overhead.

| Database | Key Strength | Consideration |
|---|---|---|
| FAISS (Meta) | Extremely flexible, high-performance, research standard | Not a full DB — needs extra engineering for production |
| Milvus | Distributed, scalable, multiple index types | High operational complexity |
| Qdrant | Strong metadata filtering, RAG-optimised, simple to operate | Less ecosystem than FAISS |
| Pinecone | Fully managed, zero ops overhead, consistent performance | Limited internal control; cost scales quickly |
| Weaviate | Strong hybrid search (dense + BM25 built-in) | More complex query interface |
| pgvector | Postgres extension — no new infrastructure needed | Lower performance at large scale |

---

---

## 7. Metadata Filtering

Metadata filtering restricts retrieval to relevant subsets before (pre-filtering) or after (post-filtering) vector search.

**Pre-filtering** (filter first, then search the smaller set):

- Faster — ANN search runs on a smaller index.

- Risk: over-filtering can hurt recall if filters are too strict.

**Post-filtering** (search first, then discard irrelevant results):

- Better recall — the full index is searched.

- Wastes compute on candidates that will be filtered out.

**Common metadata filters:**

- Document type or source

- Timestamp / version (retrieve only recent documents)

- Author or department

- Access permissions / tenant ID (multi-tenant RAG)

- Content type (prose vs. table vs. code)

> Metadata filtering is one of the highest-ROI improvements in a vanilla RAG system — it narrows the search space without changing the embedding model or retraining anything.

---

---

## 8. Multi-Tenant RAG and Access Control

In enterprise systems, different users should only retrieve from their permitted document subset. Two main approaches:

1. **Namespace / collection isolation:** Each tenant's documents live in a separate index namespace. Cleanest isolation but higher infrastructure cost.

2. **Metadata-based filtering:** All documents share one index; retrieval filters on a `tenant_id` metadata field. More efficient but relies on the vector DB correctly enforcing filters.

---
