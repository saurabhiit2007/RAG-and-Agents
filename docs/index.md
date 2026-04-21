# RAG & Agents — Knowledge Base

A technical reference covering Retrieval-Augmented Generation (RAG), LLM Agents, and Context Engineering. Built for deep interview preparation and production system design.

---

## How to Use This Knowledge Base

- Start with the **Fundamentals** sections in each topic area to build the conceptual foundation.

- Use **Advanced** sections for production-grade depth.

- Use the **Interview Questions** at the end of each page for active recall.

- Use the **Quick Reference** pages for rapid revision before interviews.

---

## Contents

### Retrieval-Augmented Generation (RAG)

| Page | What You'll Learn |
|---|---|
| [Fundamentals](RAG/fundamentals.md) | What RAG is, the core loop, RAG vs. fine-tuning, failure modes |
| [Chunking](RAG/chunking.md) | Fixed-size, recursive, semantic, and hierarchical chunking |
| [Embedding](RAG/embedding.md) | Bi-encoders, embedding models, fine-tuning embeddings |
| [Retrieval Methods](RAG/retrieval_methods.md) | BM25, dense retrieval, hybrid retrieval, RRF |
| [Indexing & Vector Databases](RAG/indexing_and_vector_database.md) | FAISS, HNSW, IVF, ANN, production vector DBs |
| [Re-Ranking](RAG/reranking.md) | Cross-encoders, Cohere Rerank, BGE rerankers |
| [Advanced RAG](RAG/advanced_rag.md) | HyDE, Self-RAG, CRAG, Adaptive RAG, GraphRAG, RAG Fusion |
| [Evaluation](RAG/evaluation.md) | Recall@k, MRR, nDCG, RAGAS, faithfulness, LLM-as-a-judge |
| [Quick Reference](RAG/quick_reference.md) | Cheat sheet for retrieval metrics, pipeline stages, failure modes |

**Supporting Concepts:**

- [TF-IDF](RAG/supporting_topics/tf_idf.md)

- [BM25](RAG/supporting_topics/bm25.md)

- [SPLADE](RAG/supporting_topics/splade.md)

- [Sentence Transformers](RAG/supporting_topics/sentence_transformers.md)

---

### LLM Agents

| Page | What You'll Learn |
|---|---|
| [Agent Fundamentals](agents/agent_fundamentals.md) | What is an agent, ReAct pattern, tool use, agent types, agentic vs. standard RAG |
| [Memory Systems](agents/memory_systems.md) | Working, episodic, semantic, and procedural memory; MemGPT; Generative Agents |
| [Planning](agents/planning.md) | ReAct, Plan-and-Execute, MCTS, LATS, Reflexion, hierarchical planning |
| [Agent Frameworks](agents/agent_frameworks.md) | LangGraph, CrewAI, AG2/AutoGen, Google ADK — comparison and trade-offs |
| [MCP & Agent Protocols](agents/mcp_and_protocols.md) | Model Context Protocol, Agent-to-Agent Protocol, Agent Cards |
| [Multi-Agent Systems](agents/multi_agent.md) | Orchestrator-worker, pipelines, debate, swarms, evaluation |
| [Agent Failure Modes](agents/agent_failure_modes.md) | Hallucinated actions, scope creep, prompt injection, loops, guardrail architecture |
| [Agentic RAG](agents/agentic_rag.md) | Self-RAG, Corrective RAG, Adaptive RAG, GraphRAG, multi-agent RAG pipelines |

---

### Context Engineering

| Page | What You'll Learn |
|---|---|
| [Context Engineering](context_engineering/ce.md) | Writing/selecting/compressing/isolating context; LLMLingua; PagedAttention; lost-in-the-middle |

---

### References

- [All References](references.md) — Full bibliography for all papers, tools, and external sources cited in this knowledge base.

---

## Key Concepts Map

```
RAG Pipeline
  └─ Indexing → Retrieval → Augmentation → Generation
        ├─ Chunking, Embedding, Vector Index
        ├─ Hybrid: BM25 + Dense + RRF
        └─ Reranking (Cross-encoder)

Advanced RAG
  ├─ Query: Rewriting, HyDE, Multi-query, Step-back
  ├─ Retrieval: Self-RAG, CRAG, Adaptive RAG
  ├─ Context: Compression, Citation-constrained generation
  └─ Graph: GraphRAG (Leiden communities)

LLM Agents
  ├─ Core loop: Reason → Act → Observe
  ├─ Memory: Working | Episodic | Semantic | Procedural
  ├─ Planning: ReAct | Plan-Execute | LATS | Reflexion
  ├─ Frameworks: LangGraph | CrewAI | AG2 | ADK
  ├─ Protocols: MCP (tools) | A2A (agents)
  └─ Safety: Guardrails | HITL | Observability

Context Engineering
  ├─ Writing: System prompts, structured output
  ├─ Selecting: Retrieval, budget allocation
  ├─ Compressing: LLMLingua, RECOMP, summarisation, caching
  └─ Isolating: Delimiters, citations, tool sandboxing
```
