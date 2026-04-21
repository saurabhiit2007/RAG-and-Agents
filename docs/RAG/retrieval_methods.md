## 1. Overview

Retrieval is the single most important factor in RAG quality. If the right document is not retrieved, the LLM cannot recover. This section covers the main retrieval algorithms from classical to neural, and how they compare.

---

---

## 2. TF-IDF

TF-IDF (Term Frequency–Inverse Document Frequency) is the foundational lexical retrieval method. It scores documents by combining two signals.

### Term Frequency (TF)

How often a term appears in the document. Higher frequency → higher score.

```
TF(t, d) = count(t in d) / total terms in d
```

Variants like logarithmic TF reduce the impact of very frequent terms.

---

### Inverse Document Frequency (IDF)

How rare a term is across the corpus. Rare terms score higher; common words ("the", "is") score near zero.

```
IDF(t) = log(N / (1 + df(t)))
```

Where N is the total number of documents and df(t) is the number containing term t.

---

### TF-IDF Score

```
TF-IDF(t, d) = TF(t, d) × IDF(t)
```

A high score indicates a term that is both locally frequent and globally distinctive.

---

**Strengths**

- Simple, no training required, interpretable, fast.

- Works well for exact and partial lexical matches.

---

**Weaknesses**

- No semantic understanding — requires exact word overlap.

- Assumes term independence (bag-of-words).

- Linear TF with no saturation — keyword stuffing inflates scores.

- Ignores word order and syntax.

---

---

## 3. BM25 (Best Matching 25)

BM25 is the go-to lexical retrieval baseline and a direct improvement over TF-IDF. It is probabilistically motivated and addresses TF-IDF's two main weaknesses: **term frequency saturation** and **document length normalisation**.

### BM25 Formula

```
BM25(d, q) = Σ IDF(t) × [tf(t,d) × (k₁ + 1)] / [tf(t,d) + k₁ × (1 - b + b × |d|/avgdl)]
```

Where:

- `tf(t, d)` — term frequency of t in document d

- `|d|` — length of document d

- `avgdl` — average document length in the corpus

- `k₁` — controls term frequency saturation (typically 1.2–2.0)

- `b` — controls length normalisation strength (typically 0.75)

---

### Key Improvements Over TF-IDF

**Term Frequency Saturation:** BM25 assumes diminishing returns for repeated terms. The first few occurrences matter most; additional repetitions contribute progressively less. This prevents keyword stuffing from dominating rankings.

**Document Length Normalisation:** Longer documents are explicitly penalised via the `b` parameter. Setting b=0 disables normalisation; b=1 applies full normalisation. TF-IDF only applies weak or implicit normalisation.

**Modified IDF:**

```
IDF(t) = log((N - df(t) + 0.5) / (df(t) + 0.5))
```
More robust for rare and common terms than the basic IDF formula.

---

### BM25 vs. TF-IDF

| Aspect | TF-IDF | BM25 |
|---|---|---|
| Term frequency | Linear — repeats always increase score | Saturated — diminishing returns past threshold |
| Length normalisation | Weak or implicit | Explicit, tunable via b |
| Tuning parameters | None | k₁ (saturation) and b (length norm) |
| Ranking quality | Good baseline | Better; closer to human judgment |
| Requires training | No | No |

---

### Example: Why BM25 Ranks Better

**Corpus:**

- D1: "deep learning deep learning deep learning tutorial"

- D2: "deep learning tutorial"

- D3: "deep learning introduction overview"

**Query:** "deep learning tutorial"

- TF-IDF ranks: D1 > D2 > D3 — D1 wins purely due to repetition of "deep learning".

- BM25 ranks: D2 > D1 > D3 — D1's score saturates; D2's shorter length gives it a boost. D2 is more concise and directly on-topic.

BM25 aligns with human intuition: repeating the same phrase doesn't make a document more relevant.

### When to Use BM25

- Exact keyword matches matter (names, IDs, error codes, product codes).

- No training budget or labelled data.

- Fast, no-GPU, interpretable baseline.

- As the sparse component of a hybrid retrieval system.

---

---

## 4. SPLADE

SPLADE (Sparse Lexical and Expansion Model) is a neural sparse retrieval model that bridges classical lexical retrieval (BM25) and dense semantic retrieval. It uses a pretrained transformer to produce sparse vector representations, and critically, it performs **learned term expansion**.

### Core Idea

BM25 relies on exact term overlap. SPLADE trains a transformer to assign weights to vocabulary terms — including terms **not present** in the input — based on semantic relevance. Despite using a neural model, the output is a sparse vector compatible with standard inverted-index infrastructure.

---

### How SPLADE Works (Step by Step)

1. **Input text** is passed through a masked language model (e.g., BERT).

2. **Vocabulary scoring:** For each token position, the model produces a score for every term in the vocabulary. The model answers: "Which vocabulary terms are relevant to this text, even if not explicitly present?"

3. **Non-linearity and sparsification:** Raw scores are transformed using ReLU (removes negatives) + log scaling (controls large activations). Max pooling across token positions produces a single sparse vector.

4. **Result:** One score per vocabulary term; most are zero. Only the most relevant terms remain active.

5. **Inverted index:** Non-zero terms are stored in a standard inverted index — identical infrastructure to BM25.

**Example expansion:**

- Input: "car repair"

- Expanded active terms: `{car: 2.1, repair: 1.9, automobile: 1.4, mechanic: 1.1, engine: 0.8}`

This allows matching a document about "automobile maintenance" even though neither query word appears in it.

---

### SPLADE Scoring Function

```
Score(t) = max over positions of log(1 + ReLU(logit_t))
```

- ReLU enforces non-negativity

- Log scaling controls large activations

- Max pooling encourages sparse activation

---

### SPLADE vs. BM25

| Aspect | BM25 | SPLADE |
|---|---|---|
| Term weighting | Hand-crafted formula (TF × IDF) | Learned by transformer |
| Semantic expansion | None — exact words only | Yes — expands to related terms |
| Index compatibility | Inverted index | Inverted index (same infrastructure) |
| Interpretability | High | Moderate |
| Requires training | No | Yes |
| Retrieval quality | Strong baseline | Stronger; approaches dense retrieval |

> Think of SPLADE as "BM25 where the term weights and expansions are learned by a language model rather than hand-crafted."

---

### When to Use SPLADE

- Want BM25 efficiency with semantic expansion.

- Existing inverted-index infrastructure that cannot be replaced.

- Queries use different vocabulary than documents.

- As the sparse component in hybrid retrieval alongside dense models.

---

---

## 5. Dense Retrieval (Bi-Encoders)

Dense retrieval uses neural embedding models to encode queries and documents into vectors; similarity is a dot product or cosine distance. Full coverage — training objectives, domain adaptation, model selection — is in [Embedding](embedding.md).

**When to use:** Natural language queries; paraphrase matching; semantic similarity matters.

**Limitation:** Weak on exact keyword matching, rare terms, and identifiers — combine with BM25/SPLADE for production systems.

---

---

## 6. Retrieval Method Comparison

| Method | Semantic Matching | Exact Match | Training Needed | Infrastructure | Best Use Case |
|---|---|---|---|---|---|
| TF-IDF | None | Good | No | Inverted index | Simple baseline |
| BM25 | None | Strong | No | Inverted index | Keyword-heavy queries; default lexical baseline |
| SPLADE | Via expansion | Strong | Yes | Inverted index | Neural sparse; efficient + semantic |
| Dense bi-encoder | Strong | Weak | Yes | Vector DB + ANN | Natural language queries; semantic similarity |
| Hybrid (dense + sparse) | Strong | Strong | Yes (dense part) | Both | Production RAG; best overall quality |

---

---

## 7. Interview Questions

**Q: Why is BM25 still widely used despite neural models being more powerful?**

A: BM25 requires no training, has no GPU inference cost, is fully interpretable, and handles exact keyword matching better than dense models. It's also very fast on inverted indexes. In hybrid systems, BM25 and dense retrieval complement each other — BM25 catches cases the dense model misses (exact terms, IDs) and dense models catch paraphrases BM25 misses.

---

**Q: What is the difference between SPLADE and a dense bi-encoder?**

A: SPLADE produces a sparse vector over the vocabulary and is indexed in an inverted index — fast, memory-efficient, and interpretable. A dense bi-encoder produces a continuous low-dimensional vector indexed in a vector DB with ANN search. SPLADE uses a neural model for semantic expansion but retains sparse representation. In practice SPLADE often outperforms BM25 and approaches dense retrieval quality, while remaining compatible with existing inverted-index infrastructure.

---

**Q: What is Reciprocal Rank Fusion (RRF) and why is it preferred over score interpolation?**

A: RRF combines ranked lists from multiple retrievers by summing 1/(k + rank) for each document across all retrievers (k is typically 60). It is preferred over linear score interpolation because it is robust to score scale differences between retrievers — BM25 scores and cosine similarities live on completely different scales. RRF requires no weight tuning and typically matches or outperforms tuned linear combinations.

---

**Q: Why might a dense retriever miss a relevant document that BM25 finds?**

A: Dense retrievers encode the entire meaning of text into a single vector — rare or highly specific terms may get diluted in the embedding. If a document is only relevant because it contains a specific product ID, error code, or proper noun, a dense embedding may not preserve that specificity. BM25's exact-match scoring handles these cases naturally. This is why hybrid retrieval consistently outperforms either method alone.

---

**Q: What preprocessing decisions most affect BM25 performance?**

A: Stopword removal, stemming/lemmatisation, and tokenisation. Removing stopwords (words like "the", "is") reduces noise. Stemming conflates "running" and "run", improving recall but potentially harming precision. BM25's k₁ and b parameters also have a significant effect and should be tuned on held-out validation data rather than left at defaults.

---