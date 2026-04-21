## 1. Overview

Vanilla RAG fails on complex queries, multi-hop reasoning, and ambiguous questions. Advanced techniques address these limitations by improving the query before retrieval, the retrieval process itself, or how context is used during generation.

---

---

## 2. Query Transformation

### Query Rewriting

Use an LLM to rephrase the original query before retrieval. Useful when the user's question is ambiguous, too short, or uses different vocabulary than the corpus.

**Example:**

- Original: "What's the deal with transformer attention?"

- Rewritten: "How does the self-attention mechanism work in transformer neural networks?"

The rewritten query is typically longer, more specific, and uses terminology that better matches document text.

---

### Multi-Query Retrieval

Generate multiple reformulations of the query, retrieve documents for each, and merge the result sets (deduplicated). Improves recall by covering different phrasings and sub-questions within the original query.

**Example sub-queries from "How does RAG reduce hallucinations?":**

- "What causes hallucinations in large language models?"

- "How does grounding in retrieved documents improve factual accuracy?"

- "What is the role of retrieval in RAG systems?"

Each sub-query may retrieve different relevant documents, increasing total coverage.

---

### HyDE (Hypothetical Document Embeddings)

Use an LLM to generate a hypothetical ideal answer to the query, embed that answer, and retrieve real documents similar to it.

**Intuition:** A generated answer lives in the same vector space as actual documents (dense, fluent text), bridging the vocabulary gap between a short query and longer document text. Short queries and long documents often have low cosine similarity even when semantically matched.

**Workflow:**

```
Query: "How does attention mechanism work?"
  │
  ▼
LLM generates hypothetical answer:
"The attention mechanism allows each token to attend to all other tokens
 in the sequence by computing query, key, and value matrices..."
  │
  ▼
Embed hypothetical answer → retrieve real documents most similar to it
```

- **Use when:** Standard retrieval misses relevant documents because query phrasing differs from document text.

- **Risk:** If the LLM hallucinates in the hypothetical answer, those errors are encoded into the retrieval vector and may retrieve wrong or misleading documents.

---

### Step-Back Prompting

For specific, detailed queries, ask the LLM to first generate a more general "step-back" question, retrieve documents for the general question, then answer the specific question using that broader context.

**Example:**

- Specific: "What was the GDP growth rate of Germany in Q3 2023?"

- Step-back: "What factors drive GDP growth in European economies?"

Retrieving for the broader question surfaces background context the specific question might not directly match.

---

## 3. Advanced Retrieval Architectures

### Parent-Document Retrieval

Index small chunks for high-precision retrieval, but when a small chunk is retrieved, expand the context by also returning its parent chunk (or surrounding window).

**Why it helps:** Resolves the tension between retrieval precision (small chunks retrieve exactly the right passage) and context completeness (the LLM needs surrounding text to fully understand that passage).

**Implementation:**

1. Index small chunks (100–200 tokens) for retrieval.

2. Store a mapping from each small chunk to its parent chunk (400–800 tokens).

3. At retrieval time, retrieve small chunks, then substitute their parent chunks in the prompt.

---

### Iterative / Recursive Retrieval

Perform multiple rounds of retrieval, where the LLM's intermediate reasoning at each step guides the next query. Particularly useful for multi-hop questions that require chaining information across multiple documents.

**Example for "Who was the mentor of the founder of DeepMind?":**

1. Retrieve: "founder of DeepMind" → learn it's Demis Hassabis.

2. Retrieve: "Demis Hassabis mentor" → learn the answer.

Vanilla RAG would try to answer this in one shot and likely fail.

---

### Self-RAG

Train the LLM to decide dynamically whether retrieval is needed, evaluate the relevance of retrieved documents, and assess whether the generated output is supported by evidence — all using special reflection tokens generated inline.

**Reflection tokens:**

- `[Retrieve]` — should retrieval happen?

- `[IsRel]` — is the retrieved document relevant?

- `[IsSup]` — is the generated text supported by retrieved evidence?

- `[IsUse]` — is the overall response useful?

This produces more selective and grounded outputs than standard RAG at the cost of more complex training.

---

### RAG Fusion

Combines multi-query generation with hybrid retrieval and fusion:

1. Generate N reformulations of the query.

2. Run dense + sparse retrieval for each reformulation.

3. Fuse all result sets with Reciprocal Rank Fusion.

4. Pass the merged, deduplicated document set to the LLM.

Addresses both query ambiguity (via multi-query) and retrieval coverage (via hybrid search) simultaneously.

---

### Graph RAG

Build a knowledge graph from documents (entities and relations), then retrieve by traversing the graph rather than pure vector similarity.

- **Strength:** Excellent for multi-hop reasoning and questions about relationships between entities.

- **Weakness:** Expensive to build and maintain; requires entity extraction and relation parsing.

For a full treatment of GraphRAG including the Leiden algorithm and Microsoft's implementation, see `docs/agents/agentic_rag.md`.

---

### Corrective RAG (CRAG)

**Paper:** [Corrective Retrieval Augmented Generation](https://arxiv.org/abs/2401.15884) (Shi et al., 2024)

Standard RAG blindly uses whatever is retrieved. CRAG adds a **retrieval evaluator** that scores retrieved document quality and triggers corrective actions:

- **Correct** (high confidence) — documents are relevant; use them with knowledge refinement (strip irrelevant passages at sentence level).

- **Incorrect** (low confidence) — documents are irrelevant; fall back to web search.

- **Ambiguous** (medium confidence) — combine internal retrieval with web search.

Knowledge refinement decomposes retrieved documents into fine-grained strips, scores each for relevance, and discards irrelevant ones before passing to the LLM. Results: CRAG achieves +15.6% over RAG baseline on PopQA.

---

### Adaptive RAG

**Paper:** [Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity](https://arxiv.org/abs/2403.14403) (Jeong et al., 2024)

A classifier routes each query to the appropriate retrieval strategy:

1. **No retrieval** — simple queries answerable from parametric knowledge.

2. **Single-step retrieval** — standard RAG.

3. **Multi-step retrieval** — iterative RAG for complex, multi-hop questions.

Reduces total retrieval calls by ~40% on benchmarks where many queries are simple, without sacrificing performance on hard queries.

---

---

## 4. Context Window Management

Even after good retrieval, how you pack documents into the context window matters significantly.

### Reorder for Primacy / Recency
Place the most relevant documents at the beginning **and** end of the context window, not the middle — to mitigate the lost-in-the-middle effect. Less relevant documents go in the middle.

---

### Context Compression
Use an LLM to extract only the sentences directly relevant to the query from each retrieved document before packing them into the prompt. Reduces noise and context window usage significantly.

**Example tools:** LLMLingua, Selective Context, RECOMP.

---

### Citation-Constrained Generation
Instruct the LLM to cite specific retrieved passages in its answer:

```
"Answer the question using only the provided context. 
 For each claim, cite the source chunk by number [1], [2], etc.
 If the answer cannot be found in the context, say 'I don't know'."
```

Forces grounding and makes hallucinations detectable.

---

### Prompt Structure

- Place the system instruction first.

- Number each retrieved chunk for easy citation.

- Place the query last (most recent in the context window).

---

---

## 5. The "Gold Standard" Production Pipeline

Combining the best techniques from across this guide:

```

1. Query rewriting / expansion
   └─ LLM rewrites the query; optionally generates a HyDE response.

2. Hybrid retrieval (parallel)
   ├─ Dense vector search (bi-encoder + ANN index)
   └─ Sparse search (BM25 or SPLADE + inverted index)

3. Score fusion
   └─ Reciprocal Rank Fusion (RRF) merges ranked lists

4. Reranking
   └─ Cross-encoder re-scores top 50–100 candidates

5. Context selection & ordering
   └─ Top 5–10 documents, ordered most-relevant first/last

6. Citation-constrained generation
   └─ LLM instructed to ground answer in retrieved text and cite sources
```

---
