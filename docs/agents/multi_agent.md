# Multi-Agent Systems

## 1. Why Multi-Agent?

A single-agent system is bounded by the context window, the capabilities of a single model, and the ability of one prompt to handle multiple specialised concerns simultaneously. Multi-agent systems address these limits by distributing work across specialised agents.

**Key motivations:**

- **Parallelism:** Independent sub-tasks run simultaneously, reducing wall-clock time.

- **Specialisation:** Each agent can be prompted (or fine-tuned) for a specific role — researcher, coder, critic, writer.

- **Context isolation:** Each agent has its own context window; the orchestrator doesn't accumulate the full context of every sub-task.

- **Scalability:** Add more agents to handle more concurrent work.

- **Reliability:** A critic agent can verify the output of a worker agent before it is accepted.

---

## 2. Core Architecture Patterns

### 2.1 Orchestrator-Worker (Hierarchical)

The most common production pattern. A **manager/orchestrator** agent receives the high-level goal, decomposes it into sub-tasks, delegates each to a **worker** agent, collects results, and synthesises a final output.

```
User Query
    ↓
[Orchestrator] — decomposes task
    ├── [Worker A: Research Agent] → retrieves documents
    ├── [Worker B: Code Agent]    → writes/runs code
    └── [Worker C: Writer Agent]  → drafts report
         ↓
[Orchestrator] — synthesises results → Final Output
```

**How orchestrator routes tasks:**

- Static routing: Orchestrator is given explicit rules ("code tasks go to Worker B").

- Dynamic routing (LLM-based): Orchestrator reads task descriptions and worker Agent Cards and decides at runtime (A2A pattern).

**Risk:** Single point of failure at the orchestrator. If it misspecifies a sub-task, downstream workers produce useless results.

---

### 2.2 Pipeline (Sequential)

Agents form a processing chain. Each agent's output is the next agent's input. No orchestrator; each agent knows its successor.

```
Raw Input → [Extractor] → [Analyser] → [Formatter] → Final Output
```

**Use when:** Tasks have a strict sequential dependency and intermediate results are well-defined. Common in document processing pipelines.

**Limitation:** Cannot parallelise. A failure at any stage blocks all downstream stages.

---

### 2.3 Peer-to-Peer (Debate / Critique)

Multiple agents of equal standing interact — challenging, critiquing, or extending each other's outputs — without a central orchestrator.

```
[Agent A] ←→ [Agent B]
     ↕             ↕
[Agent C] ←→ [Agent D]
```

**Example pattern — Society of Mind / Multi-Agent Debate:**

Paper: [Improving Factuality and Reasoning in Language Models through Multiagent Debate](https://arxiv.org/abs/2305.14325) (Du et al., 2023)

> Agents independently produce answers, then each reads the others' answers and updates its own. After multiple rounds, the agents converge on a consensus answer. This achieves ~11% improvement in mathematical reasoning over single-agent baselines.

**Critique-and-Revise pattern:**

```
[Agent A: Generator] → draft
    ↓
[Agent B: Critic]    → critique
    ↓
[Agent A: Generator] → revised draft (informed by critique)
```

This mirrors human editorial review; it improves output quality for writing, code, and analysis tasks.

---

### 2.4 Swarm (Dynamic Handoff)

Agents dynamically hand off control to each other based on the current state of the conversation or task. No fixed topology — any agent can pass to any other.

AG2 (AutoGen's successor) implements swarm mode:
```python
agent_a.register_handoff(target=agent_b, condition="if code needs review")
agent_b.register_handoff(target=agent_a, condition="if review is complete")
```

**Use when:** Tasks are inherently fluid and the appropriate specialist depends on context that only becomes apparent mid-execution.

**Limitation:** Harder to reason about and debug than hierarchical patterns.

---

## 3. Communication Between Agents

### In-Process (Same Machine)

Agents share a message bus or call each other's Python functions directly. Used in single-machine frameworks (LangGraph sub-graphs, CrewAI crews).

**Format:** Python function calls or shared state dictionaries.

### Via MCP (Model Context Protocol)

One agent exposes its capabilities as an MCP server; another connects to it as an MCP client. Enables cross-language, cross-process tool integration. See `mcp_and_protocols.md`.

### Via A2A (Agent-to-Agent Protocol)

Agents communicate via HTTP using the A2A standard. Enables cross-vendor, distributed agent networks where agents are discovered via Agent Cards. See `mcp_and_protocols.md`.

---

## 4. State Management in Multi-Agent Systems

Shared state is the hardest problem in multi-agent design. Options:

| Approach | Description | Tradeoff |
|---|---|---|
| **Shared context object** | All agents read/write a central state dict | Simple; race conditions if concurrent writes |
| **Message bus** | Agents communicate only via messages | Decoupled; harder to inspect current state |
| **Checkpoint store** | State persisted to DB (LangGraph checkpointer) | Resilient to crashes; adds I/O overhead |
| **Handoff objects** | Each agent bundles context into a structured message for the next agent | Clean; context loss if fields are omitted |

---

## 5. Evaluation Challenges

Multi-agent systems are harder to evaluate than single agents:

- A correct final output may result from flawed intermediate steps.

- A wrong final output may result from correct reasoning at every step (the task was simply impossible).

- Individual agent traces must be logged and attributed separately.

**Approaches:**

- **Step-level evaluation:** Evaluate each agent's output independently.

- **Task-level evaluation:** Evaluate the final output against a ground truth.

- **Trajectory evaluation:** Score the full sequence of actions, not just the final answer.

- **LLM-as-a-judge:** Use a separate judge LLM to score agent reasoning at each step.

---

## 6. Production Considerations

| Concern | Design Decision |
|---|---|
| Parallelism | Use async execution; independent sub-tasks run concurrently |
| Latency | Each agent-to-agent hop adds network round-trip; batch sub-tasks where possible |
| Cost | More agents = more LLM calls; use cheaper models for lower-stakes workers |
| Debugging | Log every inter-agent message with timestamps and agent IDs |
| Failure isolation | Worker failures should not crash the orchestrator; implement retries + fallbacks |
| Context limits | Each worker gets only the context it needs (not the full orchestrator context) |
