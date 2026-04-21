# RAG & Agents — Interview Q&A

A comprehensive collection of interview questions covering Retrieval-Augmented Generation, LLM Agents, and Context Engineering. Format mirrors the GenAI Interview Q&A document — each question includes a structured answer, follow-ups, and coding challenges where applicable.

---

## Chapter 1: RAG Fundamentals

---

**Q1. What problem does RAG solve that fine-tuning does not?**

RAG solves the **knowledge access problem**. LLMs have a training cutoff and fixed parametric knowledge — they cannot access information that postdates training or is not in the training corpus. Fine-tuning changes *how* the model behaves (style, reasoning, output format) but does not allow the model to look up new facts. A fine-tuned model still hallucinates when asked about events or facts outside its training data.

RAG decouples knowledge storage from model weights: the model retrieves relevant documents at inference time and grounds its answer in that retrieved evidence. The knowledge base can be updated by re-indexing new documents — no retraining required.

**Key distinction:**

- RAG: "What do the retrieved documents say about X?"

- Fine-tuning: "How should I respond to questions about X?"

> **Follow-up:** Can you use RAG and fine-tuning together?
>
> Yes, and this is common in production. Fine-tuning handles "how to respond" (instruction following, output format, tone); RAG handles "what to respond with" (factual content). A model fine-tuned for citation-constrained generation + RAG for retrieval is a common production pattern.

---

**Q2. Formally, how does RAG change the generation objective?**

Vanilla LLM generation maximises `P(y | q)` — the probability of answer `y` given only the query `q`. The model relies entirely on parametric knowledge baked into its weights.

RAG conditions generation on both the query and retrieved documents:

```
P(y | q, d₁, d₂, ..., dₖ)
```

The model generates an answer grounded in the retrieved evidence `d₁:k` rather than relying solely on its internal parameters. This reduces hallucination because incorrect parametric beliefs can be overridden by retrieved facts.

> **Follow-up:** What is the risk of this objective?
>
> If retrieval fails (wrong documents retrieved), the model generates answers conditioned on irrelevant or incorrect evidence. The model cannot distinguish good retrieval from bad retrieval without explicit verification. This is why faithfulness evaluation and retrieval quality metrics are both necessary.

---

**Q3. What are the main failure modes of vanilla RAG?**

| Failure Mode | Description | Primary Fix |
|---|---|---|
| Poor recall | Relevant documents exist but aren't retrieved | Hybrid retrieval; improve embeddings |
| Poor precision | Irrelevant documents retrieved and used | Reranking; CRAG |
| Chunking errors | Semantic meaning split across chunk boundaries | Recursive/semantic chunking; parent-doc retrieval |
| Context overflow | Retrieved context exceeds context window | Compression; selective retrieval |
| Model ignores context | LLM uses parametric knowledge instead of retrieved text | Explicit grounding instructions; Self-RAG |
| No verification | Fluent but wrong answer returned with no flag | Faithfulness scoring; citation constraints |

> **Follow-up:** Which failure is hardest to detect?
>
> "Model ignores context" — the system appears to work (fluent answer, no error) but the answer is grounded in the model's parametric knowledge rather than retrieved documents. This is detectable only via faithfulness evaluation (checking that every claim in the answer is supported by a retrieved chunk).

---

**Q4. When should you use a long-context LLM instead of RAG?**

Use a long-context LLM when:

1. The knowledge base **fits entirely in the context window** (typically ≤ 200K tokens for current frontier models).

2. The knowledge base is **stable** — infrequent updates mean the overhead of a retrieval index is not justified.

3. **Latency and cost** for a large context are acceptable for the use case.

Use RAG when:

1. The knowledge base is **larger than the context window** (millions of documents).

2. The knowledge base **changes frequently** (re-indexing is cheaper than re-generating the full context).

3. **Citations and traceability** are required (RAG produces attributable sources).

4. **Cost must scale with query** rather than with the size of the entire knowledge base.

> **Follow-up:** What are the risks of long-context LLMs?
>
> The lost-in-the-middle effect — LLMs attend less to content in the middle of long contexts. Very long prompts are also expensive (cost scales with token count) and slow. For production systems with large, changing knowledge bases, RAG remains the preferred approach even as context windows grow.

---

## Chapter 2: Retrieval and Indexing

---

**Q5. What is the difference between sparse and dense retrieval?**

**Sparse retrieval (BM25, TF-IDF):**

- Represents documents as sparse vectors of term counts/weights.

- Matches documents by **lexical overlap** (same words in query and document).

- Fast, interpretable, excellent for exact-match queries and technical terms.

- Fails on synonyms, paraphrases, or semantic similarity without lexical match.

**Dense retrieval (bi-encoders):**

- Embeds query and documents into a shared dense vector space.

- Matches by **semantic similarity** (cosine or dot product distance).

- Handles synonyms and paraphrases; generalises across phrasings.

- Slower index build (embedding each document); requires ANN index for fast retrieval.

**Hybrid (BM25 + Dense + RRF):**

- Run both in parallel; fuse ranked lists with Reciprocal Rank Fusion.

- Consistently outperforms either alone across retrieval benchmarks.

- Industry standard for production RAG.

> **Follow-up:** What is Reciprocal Rank Fusion (RRF)?
>
> RRF merges multiple ranked lists without needing score normalisation. For each document, its RRF score is the sum of `1 / (k + rank_in_list_i)` across all lists (k=60 is typical). Documents that rank well in multiple lists score highest. RRF is robust to score scale differences between BM25 and dense retrievers.

---

**Q6. What is a cross-encoder and when is it used in RAG?**

A **cross-encoder** takes a (query, document) pair as a single input and produces a relevance score. Unlike a bi-encoder that encodes query and document independently, a cross-encoder allows full attention between query and document tokens — enabling much more precise relevance judgement.

**Trade-off:** Full attention is expensive — cross-encoders cannot be pre-computed and indexed. They are used only as a **reranker** on the top-N candidates (typically top-50–100) from the initial fast retrieval step.

**Pipeline:**
```
All documents → ANN retrieval (fast, ~100ms) → top-100 candidates
    → Cross-encoder reranker (slow, ~500ms for 100 docs) → top-5–10
    → Pass to LLM
```

**When to add a reranker:** When initial retrieval precision is insufficient — retrieved documents are topically related but not precisely relevant to the query. Cross-encoders typically recover 5–15% additional precision over bi-encoder retrieval alone.

---

## Chapter 3: Advanced RAG Techniques

---

**Q7. What is HyDE and how does it bridge the query-document gap?**

**HyDE (Hypothetical Document Embeddings)** uses an LLM to generate a hypothetical ideal answer to the query, then embeds that answer rather than the original query for retrieval.

**Why it works:** A dense, fluent passage (the hypothetical answer) lives much closer in vector space to real documents on the same topic than a short, sparse user query does — even when they cover the same concept. This bridges the vocabulary and length mismatch between queries and documents.

```
Query: "How does attention mechanism work?"
  ↓
LLM generates: "The attention mechanism computes query, key, and value
matrices from input embeddings and uses scaled dot-product..."
  ↓
Embed this passage → retrieve real documents most similar to it
```

**Risk:** If the LLM hallucinates in the hypothetical answer, those errors are encoded into the retrieval vector — potentially retrieving misleading documents. Use HyDE with models that are reliable for the domain.

> **Coding challenge:**
> ```python
> def hyde_retrieval(query: str, llm, retriever) -> list[Document]:
>     hypothetical = llm.invoke(
>         f"Write a detailed answer to: {query}\nAnswer:"
>     )
>     return retriever.retrieve(hypothetical.content)
> ```

---

**Q8. What is Self-RAG and how does it differ from standard RAG?**

**Standard RAG:** Always retrieves; always uses what is retrieved; no verification.

**Self-RAG:** Trains the LLM to generate **reflection tokens** inline that control retrieval and self-assess groundedness:

| Reflection Token | Question | Values |
|---|---|---|
| `[Retrieve]` | Should I retrieve? | yes / no |
| `[IsRel]` | Is the retrieved document relevant? | relevant / irrelevant |
| `[IsSup]` | Is my generated text supported? | fully / partially / not supported |
| `[IsUse]` | Is the response useful? | 1–5 |

Self-RAG with Llama-2-13B outperforms GPT-4 on PopQA and ASQA. The model only retrieves when needed (`[Retrieve]=yes`), reducing latency for simple queries.

**Key trade-off:** Requires fine-tuning the generation model. Cannot be applied to black-box APIs. CRAG achieves similar corrective benefits without modifying the LLM.

---

**Q9. How does GraphRAG handle queries that standard vector RAG fails on?**

Standard vector RAG retrieves chunks similar to the query by cosine similarity. It fails on:

1. **Global queries** — "What are the main themes in this corpus?" No single chunk captures this.

2. **Multi-hop queries** — "How is entity A connected to event B?" The connection may span many chunks.

**GraphRAG (Microsoft, 2024)** builds a knowledge graph from the corpus:

1. Extract entities and relationships (LLM-based).

2. Apply Leiden algorithm for community detection (groups of tightly related entities).

3. Generate LLM summaries for each community.

**Query time:**

- Global queries: map-reduce over community summaries.

- Local queries: traverse graph from the most relevant entity.

**Build cost is high** (LLM calls for entity extraction + community summarisation). Best for: large corpora where thematic understanding or entity relationship queries are frequent.

---

## Chapter 4: RAG Evaluation

---

**Q10. Why is no single metric sufficient to evaluate a RAG system?**

RAG has multiple failure modes that different metrics capture:

| Metric Type | What It Catches | What It Misses |
|---|---|---|
| Recall@k | Whether relevant docs are retrieved | Ranking quality, precision |
| Faithfulness | Whether answer is grounded in retrieved docs | Whether retrieved docs are correct |
| Answer correctness | Whether answer matches ground truth | Whether grounding is the source |
| End-to-end F1 | Final answer quality | Root cause of failures |

A system can have: high recall + low faithfulness (retrieves well, then hallucinates); high faithfulness + wrong answer (correctly cites wrong source); perfect generation + poor retrieval (lucky parametric recall). All layers must be evaluated to diagnose root causes.

---

**Q11. What are the RAGAS evaluation dimensions and what does each measure?**

**RAGAS** (Es et al., 2023) provides reference-free evaluation of RAG systems using an LLM as a judge:

| Dimension | Question | Requires Ground Truth? |
|---|---|---|
| **Faithfulness** | Are all claims in the answer supported by retrieved context? | No |
| **Answer Relevance** | Is the answer on-topic for the original query? | No |
| **Context Recall** | Does the retrieved context contain what's needed to answer? | Yes (reference answer) |
| **Context Precision** | Are retrieved documents relevant, or is there noise? | No |

**Key risks of LLM-as-a-judge:**

1. **Fluency bias** — well-written hallucinations can score high.

2. **Prompt sensitivity** — scoring rubric significantly affects results.

3. **Self-preference** — models prefer outputs from the same model family.

**Mitigation:** Validate RAGAS scores against human judgments on a held-out set before using for production decisions.

> **Follow-up:** How do you build an evaluation set without labelled data?
>
> Three approaches: (1) Synthetic — LLM generates question-context-answer triples from your corpus; (2) Production logging — sample real user queries and have humans label correct answers; (3) Expert annotation — domain experts create a gold-standard test set (expensive, highest quality). Start synthetic for iteration speed; refine with human annotations before deployment.

---

**Q12. How do you diagnose whether a RAG failure is in retrieval or generation?**

Run an **oracle experiment**: manually find the correct document and inject it directly into the prompt, bypassing retrieval entirely.

- If the model answers **correctly** with the oracle document → the failure is in **retrieval** (fix: improve embeddings, use hybrid retrieval, adjust chunking).

- If the model **still fails** with the correct document in context → the failure is in **generation** (fix: improve prompting, citation constraints, grounding instructions, or model capability).

This isolates the failure mode cleanly and prevents the common error of optimising retrieval when the real problem is generation (or vice versa).

---

## Chapter 5: LLM Agent Fundamentals

---

**Q13. What is the difference between an LLM and an LLM agent?**

An **LLM** takes a fixed input and produces a single output. It answers a question in one shot.

An **LLM agent** uses an LLM as its reasoning engine but wraps it in a loop:
```
while not done:
    thought = LLM.reason(state, history, tools)
    if thought.requires_tool:
        result = tool.call(thought.tool_name, thought.args)
        history.append(result)
    else:
        return thought.final_answer
```

The agent can call external tools, observe their results, and dynamically decide the next step — repeating until the task is complete.

**Key differences:**

| Dimension | LLM | LLM Agent |
|---|---|---|
| Flow | Fixed: one input → one output | Iterative: reason → act → observe |
| External state | None | Maintains state across steps |
| Tool access | None | Calls APIs, databases, code interpreters |
| Planning | Single response | Dynamic, step-by-step |

---

**Q14. How does function calling work at the API level?**

The caller passes a list of tool schemas (JSON with name, description, parameters) alongside the user message. If the model decides a tool call is needed, instead of generating text it emits a structured JSON object:

```json
{
  "tool_call": {
    "name": "search_web",
    "arguments": {"query": "RAG benchmarks 2025", "max_results": 3}
  }
}
```

The calling framework executes the tool and appends the result as a **tool message** back to the conversation. The model then continues generating — either calling another tool or producing a final answer.

**Key design rules for tool schemas:**

- Names must be descriptive — the model uses the name and description to decide when to call.

- Avoid overlapping tool descriptions — ambiguity causes wrong tool selection.

- Mark parameters required only if the tool genuinely cannot run without them.

- Keep return formats concise and structured — avoid dumping raw HTML.

---

**Q15. What is the ReAct pattern and why is it the dominant agent architecture?**

**ReAct (Reason + Act)** (Yao et al., 2022) interleaves *Thought*, *Action*, and *Observation* steps before producing a final answer.

```
Thought: I need to find the CEO of Anthropic.
Action: search_web("Anthropic CEO 2025")
Observation: Dario Amodei is the CEO of Anthropic.
Thought: I have the answer.
Answer: Dario Amodei is the CEO of Anthropic.
```

**Why it's dominant:**

1. The *Thought* step (chain-of-thought) forces explicit reasoning before acting — reduces impulsive wrong tool calls.

2. *Observations* ground the model in real retrieved information, reducing hallucination.

3. The loop allows self-correction — if an observation is unexpected, the next thought can adapt.

**Limitations:** Linear (no backtracking); no exploration; prone to tool-call loops. Advanced alternatives: LATS (tree search), Reflexion (reflection + retry).

---

## Chapter 6: Agent Memory and Planning

---

**Q16. What are the four memory types in LLM agents?**

| Memory Type | What It Stores | Where | Example |
|---|---|---|---|
| **Working (in-context)** | Active context: task, history, tool outputs | Context window | Current conversation, scratchpad |
| **Episodic** | Specific past interactions with timestamps | Vector DB | "On task X, tool Y returned Z" |
| **Semantic** | General facts and domain knowledge | Weights or RAG index | World knowledge, domain facts |
| **Procedural** | Action policies and skills | System prompt or fine-tuned weights | "Always check docs before coding" |

**Key distinction — episodic vs. semantic:**
Episodic memory records what the agent *experienced* (a concrete interaction). Semantic memory records what the agent *knows* (general facts). Periodic reflection converts episodic memories into semantic ones, preventing the episodic store from flooding with low-level events.

> **Follow-up:** How does MemGPT extend the context window?
>
> MemGPT treats the context window like CPU RAM and external storage like disk. The agent is given explicit memory management functions (`archival_memory_search`, `archival_memory_insert`) it calls like any tool. When the context fills, old content is paged to external storage; the agent explicitly retrieves it when needed. This enables unbounded effective context.

---

**Q17. What is LATS and how does it improve over ReAct?**

**LATS (Language Agent Tree Search)** (Zhou et al., 2023) replaces ReAct's greedy single-path search with Monte Carlo Tree Search (MCTS):

1. **Selection** — pick the most promising node using UCB1.

2. **Expansion** — generate new action candidates.

3. **Evaluation** — score each with an LLM critic (not a random rollout).

4. **Backpropagation** — update scores of all nodes on the path.

5. **Reflection** — when a path fails, generate a verbal critique and use it to inform other branches.

**Results:** HotpotQA: LATS 73.2% vs. ReAct 35.1%. HumanEval (GPT-4): LATS 94.4%.

**When to use:** Tasks with high combinatorial complexity where the best answer matters more than speed. The cost is significantly more LLM calls.

---

**Q18. What is Reflexion and how does verbal reinforcement work?**

**Reflexion** (Shinn et al., 2023) adds a reflection step after a failed attempt: the agent generates a natural language critique of what went wrong, stores it in episodic memory, and uses it on the next attempt.

```
Attempt 1 → fail
Reflection: "I called the wrong API endpoint. I should check the documentation first."
  ↓ stored in memory
Attempt 2 → informed by reflection → succeed
```

**Why verbal > numerical reward:** Natural language critiques are directly interpretable by the LLM on the next attempt, providing specific corrective guidance rather than just a scalar signal.

**Results:** Improves HumanEval pass@1 from ~67% to ~88% with GPT-4.

---

## Chapter 7: Agent Frameworks and Protocols

---

**Q19. What is the core abstraction in LangGraph?**

LangGraph models agent execution as a **directed graph with cycles**:

- **Nodes:** Python functions (LLM calls, tool calls, state transforms).

- **Edges:** Transitions between nodes — unconditional or conditional (based on state).

- **State:** A typed dictionary passed through the graph; each node reads from and writes to it.

Cycles are what enable the ReAct loop — execution can return from the tools node back to the LLM node indefinitely. Conditional edges implement routing logic ("if the model called a tool, go to tools; else return to user"). Human-in-the-loop interrupt points pause execution at any node for external approval.

---

**Q20. What problem does MCP solve?**

Before MCP, every AI tool had to be written as a custom adapter for each framework — a tool for LangChain couldn't be used in Claude Desktop without reimplementation.

**Model Context Protocol (MCP)** defines a universal client-server protocol:

- **MCP Server:** A tool (database, API, file system) exposes itself once as an MCP server.

- **MCP Client:** Any MCP-compatible host (Claude, GPT-4, custom app) connects and discovers available tools automatically.

This reduces the integration problem from N×M (N models × M tools) to N+M (N hosts + M servers).

**Protocol:** JSON-RPC 2.0 over stdio (local) or HTTP+SSE (remote). Servers expose Tools, Resources, and Prompts.

> **Follow-up:** What is A2A and how does it complement MCP?
>
> A2A (Agent-to-Agent protocol, Google, April 2025) standardises agent-to-agent communication. MCP handles model→tool connections; A2A handles agent→agent delegation. In a production system: an orchestrator uses A2A to delegate to sub-agents; each sub-agent uses MCP to connect to its tools.

---

## Chapter 8: Agent Safety and Production

---

**Q21. What are the main agent failure modes in production?**

| Failure Mode | Description | Mitigation |
|---|---|---|
| Hallucinated actions | Agent fabricates tool results or invents non-existent tools | Log every tool call; compare agent's stated observations to actual returns |
| Scope creep | Agent expands beyond assigned task | Principle of least privilege; tool allowlists |
| Cascading errors | Early wrong observation poisons downstream reasoning | Verification steps between major stages; oracle experiments |
| Context loss | Key instructions forgotten in long tasks | Periodic constraint re-injection; MemGPT paging |
| Tool misuse | Right tool, wrong arguments | Schema validation before execution; few-shot examples |
| Prompt injection | Adversarial content in tool outputs hijacks behaviour | Sanitise tool outputs; safety classifier; privilege separation |
| Infinite loops | Same tool called repeatedly without progress | Loop detector; step budget; divergence detector |

> **Follow-up:** What is prompt injection specific to agents?
>
> In agents, the attack surface expands from user input to any tool output (web pages, documents, emails). An attacker who controls a webpage the agent visits can inject instructions that redirect the agent's behaviour. Mitigation: treat all tool outputs as untrusted; sanitise before context injection; use privilege separation (read tools cannot trigger write-capable tools).

---

**Q22. When should a production agent require human approval before acting?**

Use this decision framework:

| Action Type | Reversible? | HITL Required? |
|---|---|---|
| Read file / web search | Yes | No |
| Write to internal notes | Yes | No |
| Send email / Slack message | No | Yes |
| Delete file or DB record | No | Yes |
| Make financial transaction | No | Always |
| Deploy to production | No | Always |

In LangGraph: `graph.add_node("confirm", human_approval_node)` inserted before any irreversible action node. Execution pauses; the human reviews the planned action and approves or rejects.

---

## Chapter 9: Context Engineering

---

**Q23. What is context engineering?**

Context engineering is the practice of deliberately constructing the information environment (context window) that an LLM operates in — choosing what to include, how to compress it, how to sequence it, and how to isolate different components.

**Four pillars:**

| Pillar | Key Techniques |
|---|---|
| **Writing** | System prompt design, structured output schemas, prompt templates |
| **Selecting** | RAG retrieval, hybrid search, reranking, memory retrieval |
| **Compressing** | LLMLingua (20× compression, 1.5% quality loss), RECOMP, summarisation, prompt caching |
| **Isolating** | Section delimiters, numbered citations, tool output sandboxing |

Context engineering has become the primary engineering discipline for production LLM applications because the context window is now the primary artefact — not the prompt string.

---

**Q24. How does LLMLingua compress prompts and what is the trade-off?**

LLMLingua uses a small proxy LLM to score each token's conditional probability `P(token | prefix)`. Tokens that are easily predictable (high probability) carry less information and are dropped.

- **Compression ratio:** Up to 20×

- **Quality loss:** ~1.5% on downstream tasks

- **Result:** Compressed RAG context passed to the main LLM — lower latency, lower cost

**Trade-off:** Adds an LLM call for the compression step. Best when: retrieved documents are long and noisy; the main LLM's context window is a bottleneck; cost and latency matter.

---

**Q25. What is the lost-in-the-middle effect and how do you mitigate it in RAG?**

LLMs attend most strongly to content at the **beginning and end** of the context window. Content placed in the middle receives consistently less attention. Liu et al. (2023) showed 20+ percentage point accuracy drops when the key document is in the middle vs. at the start.

**Mitigation for RAG:**

- Place the most relevant documents at the **beginning** of the retrieved context block (captures attention sink).

- Place the second-most relevant at the **end** (captures recency bias).

- Less relevant documents go in the middle.

- Place the current query **last** in the overall prompt (recency bias puts the question at maximum attention).

---

## Quick Reference Cheat Sheet

### RAG Pipeline Stages

```

1. Indexing:    chunk → embed → store in vector index

2. Retrieval:   embed query → ANN search → rerank

3. Augmentation: inject top-k chunks into prompt

4. Generation:  LLM generates grounded answer
```

### Key Retrieval Metrics

| Metric | Formula | What It Measures |
|---|---|---|
| Recall@k | % queries with ≥1 relevant doc in top-k | Coverage |
| MRR | avg(1/rank of first relevant doc) | Rank of first relevant |
| nDCG | Weighted by position and graded relevance | Full ranking quality |
| Precision@k | % of top-k docs that are relevant | Noise level |

### RAGAS Dimensions

| Dimension | Reference-Free? | Measures |
|---|---|---|
| Faithfulness | Yes | Answer grounded in retrieved context |
| Answer Relevance | Yes | Answer addresses the question |
| Context Recall | No | Retrieved context covers the answer |
| Context Precision | Yes | Retrieved docs are relevant |

### Agent Memory Types

```
Working   → context window (volatile, fast)
Episodic  → vector DB (past experiences, timestamped)
Semantic  → weights or RAG index (general facts)
Procedural → system prompt or fine-tuned weights (action policies)
```

### Planning Methods at a Glance

```
ReAct        → greedy, single-path, adaptive
Plan-Execute → upfront plan, parallel steps, brittle to surprises
LATS         → tree search, expensive, best quality
Reflexion    → retry with reflection, medium cost
```

### MCP vs. A2A

```
MCP → model ↔ tool  (filesystem, database, API)
A2A → agent ↔ agent (orchestrator ↔ sub-agent)
```

### Agent Failure Mode Mitigations

```
Hallucinated actions  → log + compare actual tool returns
Scope creep           → least privilege tool allowlists
Cascading errors      → verification checkpoints
Context loss          → constraint re-injection; MemGPT
Prompt injection      → sanitise tool outputs; privilege separation
Infinite loops        → loop detector; step budget
```
