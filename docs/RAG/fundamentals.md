## 1. Overview

Large Language Models are trained on a fixed snapshot of data; knowledge is baked into model weights and cannot change without retraining. This creates three hard problems: a **knowledge cutoff** (no access to post-training events), **hallucinations** (the model generates plausible-sounding but wrong answers when it lacks a fact), and **poor domain specificity** for proprietary or niche corpora.

**Retrieval-Augmented Generation (RAG)** decouples knowledge storage from language generation. Instead of forcing the model to memorise facts, it retrieves relevant external documents at inference time and conditions generation on that retrieved context.

---

---

## 2. The Core RAG Loop

1. User submits a query.

2. A retriever searches an external knowledge base and returns the top-k most relevant chunks.

3. Retrieved chunks are injected into the prompt as context.

4. The LLM generates an answer grounded in that context.

---

---

## 3. RAG vs. Fine-Tuning — Choosing the Right Tool

This is one of the most common conceptual interview questions. The short answer: **use RAG when the problem is about knowledge access; use fine-tuning when the problem is about model behaviour.**

| Dimension | RAG | Fine-Tuning |
|---|---|---|
| Knowledge type | Dynamic, large, frequently changing | Stable, compact |
| Primary goal | Access external facts at inference time | Change reasoning style or output format |
| Cost to update | Re-index documents (cheap) | Retrain or fine-tune model (expensive) |
| Explainability | Citations traceable to source chunks | Opaque — knowledge in weights |
| Hallucination risk | Reduced (grounded in retrieved text) | Not directly addressed |
| Common use case | Enterprise Q&A, support bots, doc search | Instruction following, code style, tone |

> **In practice RAG and fine-tuning are complementary.** A model may be fine-tuned for instruction following, while RAG supplies factual grounding at runtime.

---

---

## 4. High-Level RAG Pipeline

A standard RAG system has four stages:

1. **Indexing** — documents are chunked, embedded, and stored in a vector index.

2. **Retrieval** — the user query is embedded and the most similar chunks are fetched.

3. **Augmentation** — retrieved chunks are injected into the prompt alongside the query.

4. **Generation** — the LLM generates a grounded answer conditioned on query + context.

---

---

## 5. Key Failure Modes of Vanilla RAG

| Failure Mode | Description |
|---|---|
| Poor recall | Relevant documents exist but are not retrieved |
| Poor precision | Retrieved documents are irrelevant or noisy |
| Chunking errors | Semantic meaning is fragmented across chunk boundaries |
| Context overflow | Retrieved context exceeds the model's context window |
| Model ignores context | LLM falls back on parametric knowledge despite good retrieval |
| No verification | System produces fluent but wrong answers with no detection |

> Most real-world RAG systems extend vanilla RAG to explicitly address these failure modes by adding reranking, query rewriting, verification, and feedback loops.

---

---

## 6. RAG vs. Fine-Tuning vs. Long-Context LLM

With frontier models now supporting 128K–1M token context windows, a third option exists: simply include all knowledge directly in the context.

| Dimension | RAG | Fine-Tuning | Long-Context LLM |
|---|---|---|---|
| Knowledge update | Re-index (cheap, fast) | Retrain (expensive, slow) | Update document in prompt |
| Knowledge size | Unlimited (external store) | Bounded by training data | Bounded by context window |
| Latency | Retrieval adds latency | None at inference | Higher for very long prompts |
| Cost | Retrieval + generation | Training cost (one-time) | Token cost scales with context length |
| Explainability | Citations traceable | Opaque | Traceable if documents are numbered |
| Hallucination risk | Reduced (grounded) | Not directly addressed | Reduced (but lost-in-the-middle effect) |
| Best for | Large, changing knowledge bases | Style/behaviour change | Small, stable knowledge bases |

**Decision framework:**

1. **Use RAG** if the knowledge base is large (>100K tokens), changes frequently, or requires traceability/citations.

2. **Use fine-tuning** if the problem is about model behaviour (tone, format, reasoning style) rather than knowledge access.

3. **Use long-context LLM** if the knowledge base fits in the context window AND is stable (few updates) AND latency/cost are acceptable.

4. **Combine all three** for production systems: fine-tune for behaviour, RAG for dynamic knowledge retrieval, long-context for short static reference documents.
