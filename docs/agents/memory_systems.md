# Agent Memory Systems

## 1. Why Memory Matters

A stateless LLM processes each request independently. An agent that must complete a multi-step task over time needs memory to carry forward what it has learned, avoid repeating work, and accumulate context. Memory is the mechanism through which agents simulate continuity.

The taxonomy used here follows the cognitive science literature (Tulving, 1985) and its adaptation to LLM agents in the survey by Wang et al. (2024) — see [References](../references.md).

---

## 2. Four Memory Types

### 2.1 Working Memory (In-Context)

**What it is:** The agent's active context window — everything currently in the prompt: system instructions, conversation history, tool outputs, scratchpad reasoning.

**Capacity:** Bounded by the model's context window. As of 2025, frontier models support 128K–1M tokens.

**Characteristics:**

- Fastest access (no retrieval needed — already in context).

- Volatile — cleared when the session ends.

- Subject to the *lost-in-the-middle* effect: attention degrades for content placed in the middle of a long context.

- Token-expensive: every token in working memory costs at inference time.

**Design patterns:**

- Keep the most recent observations near the end of the context (recency bias of attention).

- Compress old tool outputs before adding new ones.

- Use a scratchpad format (e.g., ReAct Thought/Action/Observation blocks) to structure the working memory.

---

### 2.2 Episodic Memory

**What it is:** Records of specific past interactions and experiences, stored externally and retrieved on demand. Analogous to human autobiographical memory — "what happened at step 7 of the task I ran last Tuesday."

**Storage:** Vector database, relational DB, or a structured log. Each episode is stored as an embedding.

**Retrieval:** At the start of a new task, the agent queries episodic memory for relevant past experiences. Retrieved episodes are injected into working memory.

**Characteristics:**

- Persistent across sessions.

- Grows over time as the agent accumulates experience.

- Supports *few-shot grounding*: past successful trajectories inform current decisions.

**Examples in practice:**

- [MemGPT](https://arxiv.org/abs/2310.08560) (Packer et al., 2023): Paged virtual context with main context and external storage. The agent manages its own memory like an OS manages RAM — moving old content to disk (external memory) and retrieving it when needed.

- [Generative Agents](https://arxiv.org/abs/2304.03442) (Park et al., 2023): Each simulated agent stores a stream of experiences with importance scores. Retrieval is scored by recency, importance, and relevance.

---

### 2.3 Semantic Memory

**What it is:** General world knowledge and domain facts — not tied to a specific episode. Analogous to factual/encyclopedic knowledge in cognitive science.

**Two sources in LLM agents:**

1. **Parametric knowledge:** Facts baked into the model weights during pretraining.

2. **Retrieved knowledge:** Documents fetched from a vector store at runtime (RAG).

**Characteristics:**

- Parametric knowledge has a training cutoff and cannot be updated without retraining.

- Retrieved knowledge can be kept current by updating the index.

- Agents must decide when to trust parametric knowledge vs. retrieve — Self-RAG addresses this with reflection tokens (see [Agentic RAG](agentic_rag.md)).

**Key distinction from episodic memory:**
Episodic memory records *what the agent experienced* (a concrete interaction). Semantic memory records *what the agent knows* (general facts). A retrieval result that is stored for reuse across sessions is semantic; the specific retrieval event that led to it is episodic.

---

### 2.4 Procedural Memory

**What it is:** Compiled knowledge about *how to act* — skills, habits, and action policies that don't require deliberate reasoning each time.

**In LLM agents, procedural memory manifests as:**

- **System prompt instructions:** General behavioral rules (how to format answers, when to ask for clarification).

- **Fine-tuned weights:** A model fine-tuned on successful agent trajectories has "procedural memory" for those tasks encoded in weights.

- **Tool usage policies:** Hard-coded rules about which tools to call in which situations.

- **Prompt templates:** Reusable prompt patterns for known sub-tasks.

**Characteristics:**

- Most efficient — no retrieval cost.

- Hardest to update — requires reprompting or retraining.

- Most reliable for well-scoped, repetitive tasks.

---

## 3. Memory Architecture Patterns

### Pattern 1: Session-Only (Stateless)
All memory is in-context. No external storage. Each session starts fresh.

**Use when:** Tasks are single-session, context window is sufficient.

**Limitation:** Cannot learn from past runs; no continuity across sessions.

---

### Pattern 2: External Memory + RAG
Agent writes important results to a vector store; retrieves relevant memories at the start of each session.

```
Start of session:
  query = current_task
  memories = vector_store.search(query, top_k=5)
  context = [system_prompt] + memories + [current_task]

End of session:
  important_results = extract_key_results(conversation)
  vector_store.upsert(important_results)
```

**Use when:** Agent must maintain continuity across many sessions; knowledge base grows over time.

---

### Pattern 3: Hierarchical Memory (MemGPT-style)

Treats the context window as "main memory" (fast, limited) and external storage as "disk" (slow, unlimited). The agent explicitly decides what to page in/out using FIFO/LRU-style operations.

```
if context_is_full:
    compress_or_page_out(oldest_content)
    page_in(most_relevant_from_storage)
```

See: [MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/abs/2310.08560)

---

### Pattern 4: Reflection and Abstraction

From [Generative Agents](https://arxiv.org/abs/2304.03442) (Park et al., 2023): periodically, the agent reflects on recent episodic memories and synthesises higher-level observations, which are stored back as semantic memories. This prevents context flooding from low-level event logs.

```
Recent episodes: [ate breakfast, walked to park, met Alice, discussed project]
  ↓ reflection (LLM summarises)
Semantic memory: "I have a collaborative relationship with Alice on the project"
```

---

## 4. Memory in Production Systems

| Concern | Design Decision |
|---|---|
| Context overflow | Compress old tool outputs; page episodic memories in/out |
| Stale memories | Add timestamps; score by recency during retrieval |
| Privacy / PII | Sanitise before writing to external stores |
| Retrieval quality | Use semantic similarity + recency + importance weighting |
| Write cost | Only write memories above an importance threshold |
