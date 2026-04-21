# Agentic RAG

## 1. From Pipeline to Agent

Standard RAG is a pipeline: retrieve → augment → generate. The retrieval step always happens; the query is always the same; no verification occurs. An **Agentic RAG** system replaces this fixed pipeline with an agent loop that decides *if*, *when*, and *how* to retrieve — and optionally verifies and improves its own outputs.

**Key capabilities Agentic RAG adds over standard RAG:**

| Capability | Standard RAG | Agentic RAG |
|---|---|---|
| Retrieval decision | Always retrieves | Decides whether retrieval is needed |
| Query strategy | Single fixed query | Multi-query, iterative, decomposed |
| Verification | None | Verifies, retries on failure |
| Multi-hop | Not supported | Supported via iterative loops |
| Tool access | Retrieval only | Retrieval + web search + code + APIs |

---

## 2. Self-RAG

**Paper:** [Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection](https://arxiv.org/abs/2310.11511) (Asai et al., 2023)

### Core Idea

Self-RAG trains the LLM to insert **reflection tokens** inline as it generates. These tokens allow the model to dynamically decide: should I retrieve? Is what I retrieved relevant? Is what I'm generating supported by the evidence?

### Reflection Tokens

| Token | Question | Values |
|---|---|---|
| `[Retrieve]` | Should retrieval happen for this generation? | `yes` / `no` |
| `[IsRel]` | Is the retrieved document relevant to the query? | `relevant` / `irrelevant` |
| `[IsSup]` | Is the generated text supported by the retrieved document? | `fully supported` / `partially supported` / `not supported` |
| `[IsUse]` | Is the overall response useful? | `5` / `4` / `3` / `2` / `1` |

### Inference

During inference, Self-RAG generates tokens step by step:

1. If it generates `[Retrieve]=yes`, it pauses, retrieves documents, and continues.

2. For each retrieved document, it generates `[IsRel]` to score relevance.

3. It generates the answer conditioned on relevant documents and produces `[IsSup]` to self-assess groundedness.

4. It generates `[IsUse]` to score overall usefulness.

Multiple retrieval-conditioned generations are scored and the best is selected.

### Results

Self-RAG with Llama-2-13B outperforms GPT-4 and Retrieval-Augmented ChatGPT on:

- Open-domain QA (PopQA, TriviaQA)

- Long-form generation (ASQA)

- Fact verification (FEVER)

**Key advantage:** Selective retrieval (only retrieves when needed) reduces latency and token cost for queries that don't require external knowledge.

---

## 3. Corrective RAG (CRAG)

**Paper:** [Corrective Retrieval Augmented Generation](https://arxiv.org/abs/2401.15884) (Shi et al., 2024)

### Core Idea

Standard RAG blindly uses whatever is retrieved. CRAG adds a **retrieval evaluator** that scores the relevance of retrieved documents and triggers corrective actions when quality is low.

### Mechanism

```
Query → Retrieve documents → Retrieval Evaluator
                                   ↓
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
              High confidence              Low confidence
          (relevant documents)          (irrelevant / ambiguous)
                    │                             │
                    ▼                             ▼
           Use retrieved docs           Web search + refine query
                    │                             │
                    └──────────────┬──────────────┘
                                   ▼
                          Knowledge refinement
                          (strip irrelevant passages,
                           decompose into fine-grained strips)
                                   ▼
                              Generate answer
```

**Three states of the evaluator:**

1. **Correct** (high confidence) — retrieved documents are relevant; use them directly.

2. **Incorrect** (low confidence) — retrieved documents are irrelevant; fall back to web search.

3. **Ambiguous** (medium confidence) — combine internal retrieval with web search.

### Knowledge Refinement

Even when documents are relevant, CRAG performs a decompose-then-filter step:

- Break retrieved documents into fine-grained knowledge strips (sentence or paragraph level).

- Score each strip for relevance to the query.

- Discard irrelevant strips before passing context to the LLM.

This reduces noise in the prompt and prevents the LLM from being confused by tangentially relevant text.

### Results (from paper)

CRAG consistently outperforms naive RAG, Self-RAG, and standard retrieval-augmented methods across:

- PopQA: +15.6% over RAG baseline

- Biography generation (factuality): +8.3%

- FEVER (fact verification): +3.7%

---

## 4. Adaptive RAG

**Paper:** [Adaptive-RAG: Learning to Adapt Retrieval-Augmented Large Language Models through Question Complexity](https://arxiv.org/abs/2403.14403) (Jeong et al., 2024)

### Core Idea

Not all queries need retrieval. Adaptive RAG learns a **classifier** that routes each query to the appropriate strategy:

1. **No retrieval** — simple queries the LLM can answer from parametric knowledge.

2. **Single-step retrieval** — standard RAG (one retrieval, one generation).

3. **Multi-step retrieval** — iterative RAG (multiple retrievals chained).

The classifier is a small LLM fine-tuned to predict query complexity. This avoids the overhead of multi-step retrieval for simple queries and the inadequacy of single-step retrieval for complex ones.

### Routing Logic

```
Query → [Complexity Classifier]
           ↓
    ┌──────┴──────┐──────────────┐
    ▼             ▼              ▼
Simple:    Moderate:       Complex:
No         Single-step     Multi-step
retrieval  RAG             iterative RAG
```

### Benefits Over Self-RAG

- **No special training required for the main LLM** — the classifier is trained separately; the generation model is unchanged.

- **More explicit routing** — the decision is made by a dedicated classifier, not reflection tokens embedded in generation.

- **Easier to audit** — routing decisions are explicit and logged.

### Results

Adaptive-RAG achieves comparable or better performance to always-retrieve baselines while reducing total retrieval calls by ~40% on benchmarks where many queries are simple.

---

## 5. GraphRAG

**Paper:** [From Local to Global: A Graph RAG Approach to Query-Focused Summarization](https://arxiv.org/abs/2404.16130) (Edge et al., Microsoft, 2024)

### Core Idea

Standard vector RAG retrieves by semantic similarity. This works well for specific fact lookup but fails for global questions about large corpora ("What are the main themes in this collection of documents?"). GraphRAG builds a **knowledge graph** from the document corpus and retrieves by traversing the graph.

### Pipeline

**Indexing phase:**

1. **Chunk documents** (standard chunking).

2. **Extract entities and relations** — use an LLM to extract entity names, types, and relationships from each chunk.

3. **Build knowledge graph** — nodes are entities; edges are relationships between entities.

4. **Community detection** — apply the Leiden algorithm to identify clusters of tightly related entities (communities).

5. **Generate community summaries** — for each community, use an LLM to write a summary of what that community represents.

**Query phase:**

- **Global queries** (themes, overview): use community summaries; generate a map-reduce answer across all relevant communities.

- **Local queries** (specific facts): traverse the graph from the most relevant entity outward, collecting related nodes and their text chunks.

### Leiden Algorithm

The Leiden algorithm (Traag et al., 2019) is used for community detection because:

- It improves on the Louvain algorithm by guaranteeing that communities are internally well-connected (no disconnected subgraphs).

- It produces a hierarchical decomposition — communities of communities — enabling multi-resolution retrieval.

### GraphRAG vs. Vector RAG

| Dimension | Vector RAG | GraphRAG |
|---|---|---|
| Retrieval unit | Text chunk | Entity + its graph neighbourhood |
| Best for | Specific fact lookup | Multi-hop reasoning, thematic queries |
| Query type | "What did document X say about Y?" | "What are the main themes?" / "How are A and B related?" |
| Index size | Proportional to chunks | Proportional to entities + edges |
| Build cost | Low (embed chunks) | High (LLM extraction of entities + edges) |
| Update cost | Re-embed changed chunks | Re-extract entities from changed chunks |

### Microsoft Implementation

Microsoft open-sourced a full GraphRAG implementation:

- GitHub: [microsoft/graphrag](https://github.com/microsoft/graphrag)

- Integrates with Azure OpenAI and Azure AI Search.

- Provides both local (entity-centric) and global (community-centric) query modes.

---

## 6. Agentic RAG Architectures

Beyond individual techniques, Agentic RAG refers to full agent architectures that orchestrate multiple retrieval strategies.

### RAG Agent with Tool Selection

```
User Query → [RAG Agent]
                ↓
         [Tool Selection]
         ┌────────────────────────────┐
         │  - vector_search(query)    │
         │  - graph_search(entities)  │
         │  - web_search(query)       │
         │  - code_exec(query)        │
         └────────────────────────────┘
                ↓
         [Retrieved context]
                ↓
         [Verification step] ← check faithfulness
                ↓
         [Generate answer]
```

### Multi-Agent RAG Pipeline

For complex research tasks, a multi-agent system where:

- **Orchestrator** receives the query and decomposes it.

- **Retrieval agents** — each specialised for a different source (vector DB, web, internal APIs).

- **Synthesis agent** — combines and deduplicates retrieved content.

- **Generation agent** — writes the final answer grounded in synthesised context.

- **Critic agent** — verifies faithfulness; rejects or flags unsupported claims.
