## Overview

Evaluating agents is fundamentally harder than evaluating a single LLM response. A plain LLM call has one input and one output. An agent executes a sequence of decisions — choosing tools, interpreting results, planning next steps — and the quality of the final answer depends on every step in that chain.

This page covers evaluation for single-agent systems and multi-agent systems separately, since multi-agent introduces additional dimensions (coordination, inter-agent communication, emergent failures) that don't exist in single-agent settings.

---

## 1. Single-Agent Evaluation

### 1.1 Why It Is Harder Than Evaluating a Single LLM Call

| Challenge | Explanation |
|-----------|-------------|
| Non-determinism | Same prompt can produce different tool-call sequences across runs |
| Variable trajectory length | One agent solves a task in 3 steps; another takes 12 — both may be correct |
| Partial credit | An agent that retrieves the right document but formats the answer wrong failed — but how badly? |
| Tool call verification | Did the agent call the right tool with the right arguments, or get lucky with the output? |
| Environment dependency | Many tasks require a live browser, code interpreter, or database — hard to reproduce exactly |

### 1.2 Outcome vs. Trajectory Evaluation

**Outcome-level:** Did the agent produce the correct final answer? Binary — easy to automate but ignores *how* the agent got there. An agent that hallucinated the right answer without using tools looks identical to one that used tools correctly.

**Trajectory-level:** Was each intermediate step correct? Did the agent call the right tools, in the right order, with correct arguments? Much richer signal but requires annotating full traces — expensive at scale.

> Use outcome metrics for benchmarking across models; trajectory metrics for debugging and improvement.

### 1.3 Key Metrics

| Metric | Definition | Notes |
|--------|-----------|-------|
| **Task Completion Rate (TCR)** | Fraction of tasks fully solved | Primary metric on most benchmarks |
| **Step Efficiency** | Avg. steps to solve a task | A system with high TCR but 3× the steps is costly in production |
| **Tool Call Accuracy** | Did the agent invoke the correct tool with correct arguments, per step? | Requires trajectory annotation |
| **Grounding Rate** | Fraction of agent claims traceable to tool outputs (not parametric knowledge) | Same concept as RAG faithfulness |
| **Retry Rate** | How often does the agent repeat the same action without progress? | High retry rate signals weak planning |

### 1.4 LLM-as-Judge for Agent Trajectories

For open-ended tasks (writing a report, debugging code), binary pass/fail is insufficient. An LLM judge evaluates:

- Was the final output correct and complete?
- Were tool calls reasonable given the task?
- Did the agent get stuck, hallucinate actions, or waste steps?

**Risk:** LLM judges reward fluent, well-structured trajectories even when factually wrong. Always validate judge scores against a human-labelled held-out set before using them for production decisions.

### 1.5 Single-Agent Benchmarks

| Benchmark | Task Type | What It Tests |
|-----------|-----------|--------------|
| **WebArena** (Zhou et al., 2023) | Web navigation (shopping, Reddit, GitLab) | Multi-step browser control on real websites |
| **SWE-bench Verified** (Jimenez et al., 2023) | GitHub issue resolution | Code agents; long-horizon software engineering |
| **AgentBench** (Liu et al., 2023) | 8 environments (OS, DB, browser, games) | Breadth across agent task types |
| **GAIA** (Mialon et al., 2023) | Real-world QA requiring tools | Factual grounding; tool selection |
| **τ-bench** (Yao et al., 2024) | Retail/airline customer service | Tool use + policy compliance in realistic workflows |

**SWE-bench Verified** is the current de facto standard for coding agents — task completion rate on it is now reported by every major agent system.

---

## 2. Multi-Agent Evaluation

### 2.1 Why Multi-Agent Is Even Harder

Single-agent evaluation has one trajectory to inspect. Multi-agent systems have **N concurrent trajectories plus the communication between them**. New failure modes emerge that don't exist in single-agent settings:

| Challenge | Explanation |
|-----------|-------------|
| Credit assignment | Which agent caused the final output to be correct or wrong? |
| Coordination failures | Agents may produce contradictory outputs, duplicate work, or deadlock waiting on each other |
| Sub-task specification quality | If the orchestrator decomposes the task incorrectly, all workers fail — but worker metrics look fine |
| Emergent errors | No individual agent is wrong, but their combined outputs produce an incorrect result |
| Communication overhead | Agents may pass malformed or incomplete context to each other, silently degrading quality |

### 2.2 Evaluation Levels

Multi-agent systems must be evaluated at three levels simultaneously:

```
System Level      →  Did the overall task succeed?
       ↓
Orchestrator Level →  Was the task decomposition correct?
                       Were sub-tasks well-specified?
       ↓
Worker Level       →  Did each agent complete its sub-task correctly?
                       Did it use the right tools?
```

Evaluating only at the system level misses orchestrator failures. Evaluating only at the worker level misses coordination failures.

### 2.3 Metrics

**System-level:**

| Metric | Definition |
|--------|-----------|
| **End-to-end TCR** | Fraction of high-level tasks fully solved by the system |
| **Coordination efficiency** | Steps taken / minimum steps needed (measures redundant or duplicated work) |
| **Time-to-completion** | Wall-clock time accounting for parallel agent execution |

**Orchestrator-level:**

| Metric | Definition |
|--------|-----------|
| **Decomposition correctness** | Are the sub-tasks necessary and sufficient for solving the high-level task? |
| **Sub-task specification quality** | Are worker instructions precise enough that each worker can execute without ambiguity? |
| **Synthesis quality** | Does the orchestrator correctly combine worker outputs into a coherent final answer? |

**Worker-level:**

Same metrics as single-agent: TCR per sub-task, tool call accuracy, grounding rate.

**Inter-agent communication:**

| Metric | Definition |
|--------|-----------|
| **Message faithfulness** | Does what one agent communicates to another accurately reflect what it found? |
| **Redundancy rate** | What fraction of tool calls across agents duplicate work already done by another agent? |
| **Contradiction rate** | How often do workers produce outputs that directly contradict each other? |

### 2.4 Coordination Failure Patterns

**Deadlock:** Agent A waits for Agent B's output before proceeding; Agent B waits for Agent A. No progress is made.

**Redundant execution:** Two workers independently call the same tool with the same arguments because the orchestrator didn't share intermediate results.

**Contradictory outputs:** Worker A concludes X; Worker B concludes ¬X. The orchestrator synthesises an incoherent answer or picks arbitrarily.

**Context loss at handoff:** Worker A produces a correct result but communicates it to Worker B incompletely (truncation, missing metadata). Worker B makes decisions on degraded information.

**Detection:** Log all inter-agent messages. Compare what each agent claims to have received vs. what the sending agent actually produced.

### 2.5 Multi-Agent Benchmarks

Dedicated multi-agent benchmarks are still emerging. Current options:

| Benchmark | Notes |
|-----------|-------|
| **GAIA** (multi-agent mode) | Tasks too complex for one agent; measures system-level completion |
| **AgentBench** (multi-agent tracks) | Some environments support multi-agent execution |
| **ChatDev / SWE-bench** (pipeline agents) | Software development with specialised coder/reviewer/tester agents |
| **CAMEL** role-playing dataset | Evaluates cooperative reasoning between two agents assigned complementary roles |

> Multi-agent benchmarks are significantly less mature than single-agent benchmarks. Most production teams build custom internal evaluation suites using their actual task distribution.

### 2.6 Practical Evaluation Strategy

Because public multi-agent benchmarks are limited, a pragmatic approach is:

1. **Decompose into sub-task unit tests.** For each worker agent type, build a targeted eval set for its sub-task (e.g., "does the research agent reliably retrieve the right document?"). These are cheap and fast.

2. **Sample full end-to-end traces.** Run the full multi-agent system on a representative task set and human-review complete traces for a sample of failures.

3. **Inject faults.** Deliberately provide a worker with a malformed input or wrong tool result, and check whether the orchestrator detects and recovers — or propagates the error silently.

4. **Monitor in production.** Log all inter-agent messages and outcomes. Contradiction rate, retry rate, and step count are the most informative signals for ongoing health.
