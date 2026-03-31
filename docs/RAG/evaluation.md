## 1. Overview

Evaluation is one of the hardest aspects of RAG. The system has multiple interacting components, no single ground-truth output, and can fail silently — generating fluent but incorrect answers. Effective evaluation requires multiple layers covering retrieval quality, generation quality, and faithfulness.

---

---

## 2. Why RAG Evaluation Is Hard

Unlike traditional NLP tasks, RAG systems:

- Do not have a single ground-truth output (multiple valid answers may exist).
- Depend on external knowledge sources that can be wrong, stale, or irrelevant.
- Can fail silently — generating fluent but factually wrong answers.
- Have multiple interacting components: a failure in retrieval causes a failure in generation, but this is hard to detect end-to-end.

No single metric is sufficient. Effective evaluation requires layered coverage.

---

---

## 3. Component vs. End-to-End Evaluation

### Component-Level Evaluation

Each module is tested independently.

- **Retrieval:** Are relevant documents retrieved? Are they ranked correctly?
- **Generation:** Given perfect context, can the model answer correctly?

| | |
|---|---|
| **Pros** | Easier to debug failures; clear error attribution; fast offline iteration |
| **Cons** | Does not capture compounding errors; may overestimate real-world performance |

---

### End-to-End Evaluation

The full pipeline is tested from user query to final answer.

| | |
|---|---|
| **Pros** | Reflects real user experience; captures interaction effects between components |
| **Cons** | Hard to diagnose root causes; more expensive and noisy |

> Strong systems use both — component evaluation during development, end-to-end evaluation before deployment.

---

---

## 4. Retrieval Metrics

### Recall@k

Fraction of queries for which at least one relevant document appears in the top-k retrieved results.

- **Why it matters:** If recall is low, generation cannot recover. Especially critical for factual QA.
- **Limitation:** Binary notion of relevance; does not consider ranking quality within top-k.

---

### Mean Reciprocal Rank (MRR)

Measures how early the first relevant document appears in the ranked list. Score = average of 1/rank across queries.

- **Why it matters:** Rewards systems that rank relevant documents earlier; useful when only one document is needed.
- **Limitation:** Ignores multiple relevant documents.

---

### nDCG (Normalised Discounted Cumulative Gain)

Measures quality of the full ranked list using graded relevance, penalising relevant documents that appear lower.

- **Why it matters:** More realistic for multi-document relevance; handles graded (not just binary) relevance labels.
- **Limitation:** Requires graded relevance annotations; more complex to compute and interpret.

---

### Precision@k

Fraction of top-k retrieved documents that are relevant.

- **Why it matters:** Complements recall — high precision means less noisy context for the LLM.
- **Limitation:** Must be considered alongside recall; a system can have high precision@3 with low recall.

> High Recall@k is often more critical than precision in RAG retrieval, because the LLM can filter irrelevant context — but it cannot invent missing information.

---

---

## 5. Generation Quality Metrics

| Metric | What It Measures | Limitation |
|---|---|---|
| Exact Match (EM) | Exact string match with reference answer | Too strict for NL generation; penalises valid paraphrasing |
| F1 Score (token overlap) | Token-level overlap with reference | Surface-level; misses semantic equivalence |
| BLEU / ROUGE | N-gram overlap with reference text | Poorly correlates with factual correctness; rewards fluency |
| BERTScore | Semantic similarity via contextual embeddings | Better than n-gram but still not factuality-aware |

> These metrics primarily measure fluency and surface similarity, not truthfulness. A hallucinated answer can score well if it is fluent and partially overlaps with the reference.

---

---

## 6. Faithfulness and Groundedness

The most critical RAG-specific evaluation dimension. A system can score well on generation metrics while still hallucinating — generating correct-sounding text not supported by the retrieved documents.

### Faithfulness
**Question:** Is every claim in the answer supported by the retrieved context?

- Measured by sentence-level entailment checks or LLM-as-a-judge prompting.
- Failure mode: Correct-sounding claims that are not in any retrieved document.

---

### Groundedness
**Question:** Does every specific claim in the answer trace back to a retrieved source?

- Measured by claim extraction followed by source matching or citation validation.
- Failure mode: Answers that are correct (by coincidence or parametric knowledge) but unsupported by retrieved text.

---

### Answer Relevance
**Question:** Does the answer actually address the original question?

- Measured by LLM-as-a-judge or semantic similarity between answer and query.

---

### Context Relevance
**Question:** Were the retrieved documents actually relevant to the query?

- Measured by LLM-based relevance scoring per retrieved chunk.

---

## 7. LLM-as-a-Judge (RAGAS Framework)

Using an LLM to evaluate RAG outputs is increasingly the standard approach. **RAGAS** is a widely-used framework evaluating four dimensions without requiring ground-truth labels for generation:

| Dimension | Question Answered |
|---|---|
| Faithfulness | Are all claims in the answer supported by retrieved context? |
| Answer Relevance | Is the answer on-topic for the original query? |
| Context Recall | Does the retrieved context contain what's needed to answer? (Needs reference answer) |
| Context Precision | Are retrieved documents relevant, or is there noise? |

**Benefits:** Scales without human labelling; captures semantic nuance beyond lexical overlap.

**Risks:**

- Bias towards fluent answers — LLM judges may reward well-written hallucinations.
- Sensitivity to prompt design — scoring rubrics matter significantly.
- Self-preference bias — models tend to rate outputs from similar architectures more favourably.

**Best practice:** Validate LLM-as-a-judge scores against human judgments on a held-out set before trusting them for production decisions.

---

---

## 8. Human Evaluation Protocols

Human evaluation remains the gold standard for RAG systems.

**Common criteria:** Correctness, completeness, faithfulness, clarity, usefulness.

**Protocol design:**

- Blind evaluation (evaluators don't know which system produced which answer).
- Multiple annotators per example (typically 3).
- Measure inter-annotator agreement (Cohen's Kappa).

**Tradeoffs:** High cost; low scalability; slow iteration — but irreplaceable for final validation.

---

---

## 9. Common RAG Failure Types and Root Causes

| Failure Type | Diagnosis | Fix |
|---|---|---|
| Relevant doc not retrieved | Low Recall@k | Improve embeddings; use hybrid retrieval; adjust chunk size |
| Retrieved but not used by LLM | Good recall, low faithfulness | Improve prompt; citation constraints; rerank more aggressively |
| Partial hallucinations | Mixed faithful + invented claims | Faithfulness scoring; instruction-tune with grounding |
| Over-reliance on parametric knowledge | Model ignores retrieved context | Explicit grounding instructions; Self-RAG |
| Stale or contradictory sources | Corpus not updated | Add timestamps; filter by recency; update index |

---

---

## 10. Building an Evaluation Dataset

**Challenge:** Creating reliable ground-truth labels for RAG is expensive.

**Approaches:**

1. **Synthetic generation:** Use an LLM to generate questions from your document corpus, creating question–context–answer triples. Fast and free, but synthetic questions may not match real user queries.
2. **Production logging:** Sample real user queries and have humans label relevant documents and correct answers. Most realistic, but requires live traffic.
3. **Expert annotation:** For high-stakes domains (medical, legal), pay subject matter experts to create a gold-standard test set. Expensive but highest quality.

---

---

## 11. Interview Questions

**Q: Why is no single metric sufficient to evaluate a RAG system?**

A: RAG has multiple failure modes that different metrics capture: retrieval metrics (recall, nDCG) measure whether the right documents are found; generation metrics (EM, F1) measure answer quality given perfect context; faithfulness metrics measure whether the answer is grounded in retrieved text; end-to-end metrics capture the combined effect. A system can have high recall but low faithfulness (retrieves well, then hallucinates). You need all layers to diagnose root causes.

---

**Q: What is the difference between faithfulness and answer correctness?**

A: Faithfulness measures whether the answer is supported by retrieved context — an answer can be wrong if the retrieved context is wrong, but still be "faithful". Answer correctness measures whether the answer matches a known ground truth — an answer can be correct but use parametric knowledge rather than retrieved context. Ideally you want both: correct and grounded in retrieved text.

---

**Q: How would you build an evaluation set for a new RAG system with no existing labelled data?**

A: Three approaches: 

(1) Synthetic generation — use an LLM to generate questions from your corpus, creating question-context-answer triples; 
(2) production logging — sample real user queries and have humans label relevant documents and correct answers; 
(3) expert annotation — for high-stakes domains, pay subject matter experts to create a gold-standard test set. 

Start with synthetic data for fast iteration and refine with human annotations before deployment.

---

**Q: What are the risks of using LLM-as-a-judge for evaluation?**

A: Three main risks: 

(1) Fluency bias — LLMs tend to prefer well-written answers even if they are less factually accurate; 
(2) Prompt sensitivity — the scoring rubric significantly affects scores and must be carefully designed; 
(3) Self-preference — when the same model family is used for generation and evaluation, it tends to rate its own outputs more favourably. Mitigate by using a different model family for judging than for generation, and always validate against human judgments on a held-out set.

---

**Q: How do you diagnose whether a RAG quality problem is in retrieval or generation?**

A: Run an oracle experiment: manually find the correct document and inject it directly into the prompt, bypassing retrieval entirely. If the model produces a correct answer with the oracle document, the problem is in retrieval. If the model still fails with the correct document in context, the problem is in generation (prompting, model reasoning, or context integration). This isolates the failure mode clearly.

---