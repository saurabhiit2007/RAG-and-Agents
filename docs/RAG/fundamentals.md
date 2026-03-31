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

## 6. Interview Questions

**Q: What problem does RAG solve that fine-tuning does not?**

A: RAG solves the knowledge access problem — it lets the model use information that wasn't in the training set, or that changes frequently. Fine-tuning changes how the model behaves (style, reasoning, format) but does not give it a way to look things up. A fine-tuned model still hallucinates when asked about facts outside its training data.

---

**Q: Can you use RAG and fine-tuning together?**

A: Yes, and this is common in production. A model might be fine-tuned for instruction following or a specific output format, and RAG provides the factual grounding at query time. Fine-tuning handles "how to respond"; RAG handles "what to respond with".

---

**Q: What are the main failure modes in a vanilla RAG system?**

A: The biggest failure is retrieval failure — the right document exists but isn't retrieved (poor recall) or irrelevant documents are retrieved (poor precision). Other failures include chunking errors that fragment context, context window overflow, the model ignoring or hallucinating over retrieved text, and the lack of any verification step.

---

**Q: Formally, how does RAG change the generation objective?**

A: Vanilla LLM generation is P(y | q) — the answer depends only on the query. RAG conditions generation on both the query and retrieved documents: P(y | q, d₁:k). The model reasons over provided evidence rather than relying solely on its internal parameters.

---