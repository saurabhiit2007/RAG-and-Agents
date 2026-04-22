# Agent Planning

## 1. What Is Planning in LLM Agents?

Planning is the mechanism by which an agent decides what sequence of actions to take to achieve a goal. It sits between the reasoning brain (LLM) and the action space (tools).

**Two broad paradigms:**

| Paradigm | Description | Example |
|---|---|---|
| **Reactive** | Decide the next action only after observing the current state | ReAct |
| **Deliberative** | Generate a full plan upfront, then execute it | Plan-and-Execute |

Neither is strictly better — reactive plans adapt to unexpected observations; deliberative plans are more efficient when the task structure is known.

---

## 2. ReAct (Reason + Act)

**Paper:** [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.11610) (Yao et al., 2022)

The foundational pattern for production agents. The model interleaves *Thought*, *Action*, and *Observation* in a loop.

```
Thought: I need to find the population of Tokyo.
Action: search_web("Tokyo population 2025")
Observation: Tokyo metropolitan area population is approximately 37.4 million.
Thought: I have the answer.
Answer: Tokyo's population is approximately 37.4 million.
```

**Why ReAct works:**

- The *Thought* step (chain-of-thought) forces explicit reasoning before acting, reducing impulsive wrong tool calls.

- *Observations* ground the model in retrieved facts, reducing hallucination.

- Each step can adapt based on what the previous step returned.

**Limitations:**

- Linear — no backtracking if a tool call returns unexpected results.

- No exploration — commits to the first plausible path.

- Prone to tool-call loops (repeatedly calling the same tool).

- Degrades on tasks requiring >5–6 steps.

**Mitigation:** Add a loop detector (track the last N tool calls; abort if the same call is repeated) and a max-step budget.

---

## 3. Plan-and-Execute

**Paper:** [Plan-and-Solve Prompting](https://arxiv.org/abs/2305.04091) (Wang et al., 2023)

First generate a complete multi-step plan (all steps), then execute steps sequentially (or in parallel where independent).

```
Phase 1 — Plan:
  LLM generates: [Step 1: Search for X, Step 2: Summarise results,
                  Step 3: Cross-reference with Y, Step 4: Write report]

Phase 2 — Execute:
  For each step, call the relevant tool and collect results.
```

**Advantages over ReAct:**

- Better for tasks with predictable structure (report generation, data pipelines).

- Enables parallel execution of independent steps.

- Plan can be reviewed and edited before execution (human-in-the-loop checkpoint).

**Disadvantages:**

- Plan becomes stale if early steps return unexpected results.

- Requires the LLM to accurately model the full task graph upfront.

- Poor for exploratory tasks where the path depends on discoveries.

**Hybrid:** Many production systems use Plan-and-Execute with a re-planning step: if a step fails or returns an unexpected observation, the planner regenerates the remainder of the plan.

---

## 4. Tree Search: MCTS and LATS

ReAct and Plan-and-Execute are linear — they commit to one path and never backtrack. For tasks where the optimal sequence of actions is genuinely uncertain, tree-search methods explore multiple alternatives before committing.

### 4.1 Monte Carlo Tree Search (MCTS) for LLMs

#### The Core Intuition

Imagine the agent's task as a maze. ReAct walks down one corridor and if it hits a dead end, it's stuck. MCTS instead builds a **map of the maze as it explores** — it keeps track of every junction it has visited, how promising each branch turned out to be, and uses that to decide where to explore next.

In agent terms, the "maze" is a tree of possible action sequences:

```
                        [Start: user question]
                               │
              ┌────────────────┼────────────────┐
              │                │                │
        [search_web]     [read_docs]      [run_code]      ← possible first actions
              │                │
        ┌─────┴──────┐    ┌────┴─────┐
        │            │    │          │
   [summarise]  [search   [extract  [ask
                 again]    table]    user]                 ← possible second actions
```

Each **node** is a state (what has happened so far). Each **edge** is an action the agent can take. MCTS explores this tree intelligently — not randomly, not exhaustively — to find the best path.

---

#### The Four Phases (Concrete Example)

Say the task is: *"Find the revenue of Apple in Q3 2024 and compare it to Q3 2023."*

**Phase 1 — Selection: Pick which node to expand next**

MCTS maintains a score for every node it has already visited. It walks down the tree from the root, at each junction picking the child with the highest UCB1 score:

```
UCB1 = (average value of node) + C × √(ln(parent visits) / node visits)
```

The first term rewards paths that have been good so far (**exploitation**). The second term rewards paths that haven't been explored much yet (**exploration**). C is a constant that controls the balance — higher C means more exploration.

In practice: if MCTS tried `search_web → summarise` twice and it scored 0.4 both times, but `search_web → search_again` was only tried once, UCB1 will push it toward trying `search_again` next — even if its current score is lower.

> **Key point:** "Policy" here means the UCB1 selection formula — it is **not** a trained neural network. MCTS is a search algorithm, not a learning algorithm.

---

**Phase 2 — Expansion: Try a new action**

At the selected node, the LLM generates one or more new possible next actions. These become new child nodes in the tree.

```
Selected node: [search_web("Apple Q3 2024 revenue")]
                        │
          Expansion generates 3 children:
          ├── [search_web("Apple Q3 2023 revenue")]
          ├── [read_url("apple.com/investor-relations")]
          └── [summarise(search_result)]
```

---

**Phase 3 — Simulation (Rollout): Estimate how good this new node is**

From the newly expanded node, run a fast heuristic rollout to the end of the task to estimate its value. In classic MCTS (chess, Go) this means playing random moves to the end of the game. For LLM agents it means:

- Either: ask an LLM critic *"Given the state so far, how likely is this path to succeed? Score 0–1."*
- Or: run a cheap, abbreviated version of the remaining task to get an outcome.

The simulation gives a **value estimate** for the new node without fully committing to it.

---

**Phase 4 — Backpropagation: Update the whole path**

> **Terminology note:** This has nothing to do with neural network gradient backpropagation. In MCTS, "backpropagation" means propagating the value estimate back up the tree — updating the scores of every node on the path from the newly expanded node back to the root.

```
New node value: 0.8

Backpropagate:
  [read_url] node: update average value → was 0.5, now 0.65
  [search_web] node: update average value → was 0.4, now 0.52
  [root] node: update → was 0.4, now 0.53
```

Now the tree "knows" that the `search_web → read_url` path is more promising than it previously estimated. Next time Selection runs, UCB1 will favour this branch.

---

#### The Full Loop

These four phases repeat for a fixed budget (e.g., 50 iterations). At the end, the agent commits to the **highest-value path** found, not just the first one it tried.

```
Repeat N times:
  1. Selection  → pick the most promising unexplored node
  2. Expansion  → generate new possible actions from it
  3. Simulation → estimate value of that new node
  4. Backprop   → update all ancestors with the new value

After N iterations:
  → Follow the path with the highest average value
```

---

#### MCTS vs ReAct vs Plan-and-Execute

| | ReAct | Plan-and-Execute | MCTS |
|---|---|---|---|
| Path explored | 1 (greedy) | 1 (upfront plan) | Many (tree) |
| Backtracking | No | Re-plan on failure | Yes — built in |
| Cost | Low | Low–Medium | High (N × LLM calls) |
| Best for | Simple tasks | Known structure | Hard, uncertain tasks |

---

### 4.2 LATS (Language Agent Tree Search)

**Paper:** [Language Agent Tree Search (LATS)](https://arxiv.org/abs/2310.04406) (Zhou et al., 2023)

LATS combines MCTS with LLM-based reflection. Key differences from standard MCTS:

- **Value function:** An LLM evaluator scores each node (rather than a random rollout).

- **Reflection:** When a path fails, the LLM generates a natural language critique of why it failed, which is appended to the prompt for subsequent search paths.

- **Backpropagation uses LLM scores:** Rather than win/loss, each state is scored on a [0,1] scale by a critic LLM.

**Results from the paper:**

- HotpotQA: LATS achieves **73.2%** vs. ReAct's **35.1%**.

- WebArena: LATS achieves **40.59%** average improvement over zero-shot chain-of-thought.

- Programming tasks: LATS with GPT-4 achieves **94.4%** on HumanEval.

**When to use LATS:**

- Tasks with high combinatorial complexity (code generation, multi-hop reasoning).

- When failure is expensive and getting the best answer matters more than speed.

- When you can afford the extra LLM calls (LATS uses significantly more tokens than ReAct).

---

### 4.3 ReAcTree

A simpler variant of tree search for agents: run multiple parallel ReAct chains, score them with an LLM critic at each step, and prune low-scoring branches. Cheaper than full MCTS because it doesn't require rollouts to completion.

---

## 5. Hierarchical Planning

For complex long-horizon tasks, flat planning (all actions at the same level of abstraction) becomes unwieldy. Hierarchical planning introduces multiple levels:

```
High-level plan (Manager agent):

  1. Research the topic.

  2. Synthesise findings.

  3. Write the report.

Low-level plan (Worker agents, for step 1):
  1a. Search for primary sources.
  1b. Read each source.
  1c. Extract key claims.
  1d. Verify claims against secondary sources.
```

The manager orchestrates; workers execute. This is the basis of multi-agent architectures (see [Multi-Agent Systems](multi_agent.md)).

**Advantages:**

- Separates concerns — manager doesn't need to know tool details.

- Workers can be specialised (one for web search, one for code execution).

- Steps at the same level can often run in parallel.

---

## 6. Self-Refinement and Reflection

**Paper:** [Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366) (Shinn et al., 2023)

Rather than backtracking during planning, Reflexion adds a post-hoc reflection step: after a failed attempt, the agent generates a verbal critique of what went wrong, stores it in episodic memory, and retries.

```
Attempt 1 → fails
Reflection: "I called the wrong API endpoint. Next time I should check the docs first."
  ↓ stored in episodic memory
Attempt 2 → informed by reflection → succeeds
```

**Key insight:** Verbal feedback (natural language critique) is often more effective than numerical reward signals for LLM-based agents, because the critique is directly interpretable by the LLM on the next attempt.

**Results:** Reflexion improves pass@1 on HumanEval from 67% to 88% (GPT-4 baseline).

---

## 7. Comparison Table

| Method | Search Strategy | Backtracking | Best For | Cost |
|---|---|---|---|---|
| ReAct | Greedy (one path) | None | Simple, predictable tasks | Low |
| Plan-and-Execute | Upfront plan, linear exec | Re-plan on failure | Structured tasks with known steps | Low–Medium |
| LATS | Tree (MCTS + reflection) | Full | Hard reasoning, code gen | High |
| Reflexion | Greedy + retry | Post-hoc (retry) | Tasks with recoverable failures | Medium |
| Hierarchical | Decomposed (manager/worker) | Per-worker | Long-horizon, multi-domain | High |
