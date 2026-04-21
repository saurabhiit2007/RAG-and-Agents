### 1. Overview

SPLADE (Sparse Lexical and Expansion Model) is a sparse neural retrieval model that combines the strengths of traditional lexical methods like BM25 with the semantic generalization of neural models. It produces sparse, interpretable representations while enabling semantic term expansion using pretrained language models.

SPLADE is especially popular in modern retrieval and RAG systems as a drop in replacement or complement to BM25.

---

### 2. Core Idea Behind SPLADE

Classical sparse retrievers rely on exact term overlap. Dense retrievers capture semantics but lose interpretability and efficiency of inverted indexes.

SPLADE bridges this gap by:

- Using a transformer encoder to generate sparse vectors

- Expanding queries and documents with semantically related terms

- Keeping representations compatible with inverted indexes

Each document and query is represented as a weighted bag of vocabulary terms, where weights are learned rather than hand engineered.

---

### 3. How SPLADE Works

### Step 1: Input Text

SPLADE processes text in the same way as standard transformer models.

**Example document:** "Neural retrieval models improve search quality"

**Example query:** "better search models"

Both documents and queries go through the same pipeline.

### Step 2: Transformer Encoding

The input text is passed through a masked language model such as BERT.

The model outputs contextualized embeddings for each token. Unlike dense retrieval, SPLADE does not pool these embeddings into a single dense vector.

Instead, it projects them into the **vocabulary space**.

### Step 3: Vocabulary Level Scoring

For each token position, the model produces a score for every term in the vocabulary.

Conceptually, the model answers:
> Which vocabulary terms are relevant to this text, even if they do not appear explicitly?

**Example high scoring terms for the document might be:** neural, retrieval, search, information, ranking, models

This is where semantic expansion happens.

### Step 4: Non Linearity and Sparsification

Raw scores are transformed using:

- ReLU to remove negative values

- Log scaling to control large activations

Then, **max pooling across token positions** is applied.

This results in:

- One score per vocabulary term

- Many terms having zero weight

Only the most relevant terms remain active.

### Step 5: Sparse Vector Representation

The final output is a sparse vector over the vocabulary.

Example representation:
{
search: 2.1,
retrieval: 1.8,
neural: 1.5,
ranking: 0.9
}


This representation:

- Is sparse like BM25

- Encodes semantics like neural models

- Is interpretable as weighted terms

---

### Step 6: Indexing with Inverted Index

Each non-zero term is added to an inverted index.

For each term, the index stores:

- Document IDs

- Term weights

This allows fast retrieval using standard sparse indexing infrastructure.

---

### Step 7: Query Processing

Queries go through the exact same steps:

- Transformer encoding

- Vocabulary scoring

- Sparsification

- Sparse vector creation

Example query expansion:

"better search models"
→ {search, retrieval, ranking, information}


### Step 8: Retrieval and Scoring

Document relevance is computed using a dot product between sparse query and document vectors.

Only overlapping non zero terms contribute to the score, making retrieval efficient.

Documents with strong lexical or semantic overlap score highest.

### Why This Works Better Than BM25

### Learned Term Weights

BM25 uses hand crafted formulas.  
SPLADE learns which terms matter directly from data.

### Semantic Expansion Without Dense Vectors

SPLADE can match:

query: "car repair"
document: "automobile maintenance"

Even without exact word overlap.

### Sparsity Preserves Efficiency

Despite using transformers:

- Storage remains sparse

- Retrieval uses inverted indexes

- Latency stays manageable

---

### Mental Model for Interviews

Think of SPLADE as:
> BM25 where the term weights and expansions are learned by a language model instead of being manually designed.

---

### 4. SPLADE Scoring Function

For a document or query, SPLADE computes:

Score(t) = max over positions of log(1 + ReLU(logit(t)))

Key properties:

- ReLU enforces non negativity

- Log scaling controls large activations

- Max pooling encourages sparse activation

Only a small subset of vocabulary terms receive non-zero weights.

---

### 5. Learned Term Expansion

Unlike BM25 or TF IDF, SPLADE can assign weight to terms that do not explicitly appear in the text.

Example:

- Query: "car repair"

- Expanded terms: "automobile", "mechanic", "engine"

This improves recall while preserving lexical matching behavior.

---

### 6. Where SPLADE Is Used

SPLADE is commonly used in:

- Neural information retrieval

- Hybrid search systems

- RAG first stage retrieval

- Enterprise and domain specific search

- Large scale retrieval where dense vectors are costly

It is especially useful when inverted index compatibility is required.

---

### 7. Strengths of SPLADE

- Sparse and interpretable representations

- Semantic expansion improves recall

- Compatible with inverted indexes

- Strong performance compared to BM25

- Lower storage cost than dense embeddings

SPLADE often outperforms BM25 without sacrificing efficiency.

---

### 8. Limitations and Caveats

- Requires pretrained transformer models

- Higher indexing cost than BM25

- Vocabulary size affects memory usage

- Inference is slower than classical sparse methods

- Requires careful regularization to control sparsity

Despite sparsity, SPLADE is still more expensive than purely lexical methods.

---

### 9. Practical Considerations

- Regularization is critical to maintain sparsity

- Index size depends on vocabulary and pruning thresholds

- Query time expansion increases recall but adds latency

- Often combined with BM25 or dense retrievers

- Fine-tuning on domain data improves performance

SPLADE is typically deployed where quality gains justify added complexity.

---

### 10. SPLADE vs BM25

| Aspect | BM25 | SPLADE |
|------|------|--------|
| Term weighting | Hand crafted | Learned |
| Semantic expansion | No | Yes |
| Sparsity | Sparse | Sparse |
| Interpretability | High | Moderate |
| Retrieval quality | Strong | Stronger |

SPLADE can be viewed as a neural generalization of BM25.

---

### 11. SPLADE in Modern RAG Pipelines

SPLADE is often used as:

- A semantic sparse retriever

- A complement to dense embeddings

- A first stage retriever before reranking

- A fallback when dense retrieval misses lexical matches

Hybrid systems frequently combine SPLADE, BM25, and dense retrieval.

---

### 12. Interview Perspective

For interviews, emphasize:

- Why SPLADE is still sparse despite being neural

- How learned term expansion improves recall

- Compatibility with inverted indexes

- Tradeoffs between BM25, SPLADE, and dense retrieval

- Its role in modern RAG architectures

---