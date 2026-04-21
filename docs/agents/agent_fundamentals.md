# Agent Fundamentals

## 1. What Is an LLM Agent?

An **LLM agent** is a system that uses a language model as its reasoning engine to autonomously plan and execute multi-step tasks by choosing and calling external tools, observing their results, and deciding on subsequent actions — rather than just generating a single text response.

The key distinction from a plain LLM call:

| Plain LLM | LLM Agent |
|---|---|
| Single input → single output | Iterative: reason → act → observe → reason |
| No external state | Maintains state across steps |
| No tool access | Calls tools (APIs, search, code, databases) |
| Deterministic flow | Plans dynamically at runtime |

An agent can be thought of as a loop:

```
while not done:
    thought = LLM.reason(current_state, history, tools)
    if thought.requires_tool:
        result = tool.call(thought.tool_name, thought.args)
        history.append(result)
    else:
        return thought.final_answer
```

---

## 2. Core Components of an Agent

Every LLM agent has five logical components:

### 2.1 Brain (LLM)
The language model that performs reasoning, planning, and decision-making. It decides *what to do next* at each step.

### 2.2 Memory
State maintained across steps. May include:

- **In-context (working) memory** — the current conversation/scratchpad

- **External memory** — a vector store or database for long-term recall
(See `memory_systems.md` for full taxonomy.)

### 2.3 Tools
External capabilities the LLM can invoke. Examples:

- Web search (Tavily, Brave Search API)

- Code execution (Python REPL, sandboxed environments)

- Database queries (SQL, vector stores)

- API calls (weather, calendar, email)

- File read/write

### 2.4 Planning
The strategy for decomposing a goal into steps. May be reactive (ReAct) or deliberative (MCTS, hierarchical).
(See `planning.md` for full coverage.)

### 2.5 Action Space
The set of allowed actions (tools) the agent can take. Defines the scope of what the agent can do and is the primary safety control point.

---

## 3. Tool Use and Function Calling

### Function Calling (Structured Tool Use)
Modern LLMs natively support function calling: given a set of function definitions (in JSON schema), the model can emit a structured call instead of plain text.

**Example schema passed to the model:**
```json
{
  "name": "search_web",
  "description": "Search the web for recent information",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "Search query"},
      "max_results": {"type": "integer", "default": 5}
    },
    "required": ["query"]
  }
}
```

**Model output (instead of plain text):**
```json
{
  "tool_call": {
    "name": "search_web",
    "arguments": {"query": "RAG latest benchmarks 2025", "max_results": 3}
  }
}
```

The calling framework executes the function and returns the result back to the model as a tool message.

### Key Design Decisions for Tool Schemas

- **Names must be descriptive** — the model uses the name and description to decide when to call the tool.

- **Avoid overlap** — two tools with similar descriptions cause the model to choose incorrectly.

- **Required vs optional parameters** — only mark parameters required if the tool genuinely cannot run without them.

- **Return format** — keep tool returns concise and structured; avoid dumping 10KB of raw HTML.

---

## 4. The ReAct Pattern

**ReAct (Reason + Act)** (Yao et al., 2022) is the foundational pattern for most production agents. The model interleaves *Thought*, *Action*, and *Observation* steps before producing a final answer.

```
Thought: I need to find the current CEO of OpenAI.
Action: search_web("current CEO of OpenAI 2025")
Observation: Sam Altman is the CEO of OpenAI as of 2025.
Thought: I have the answer.
Answer: Sam Altman.
```

**Why ReAct works:**

- The *Thought* step forces the model to reason explicitly before acting (reduces impulsive wrong tool calls).

- *Observations* ground the model in real retrieved information, reducing hallucination.

- The loop allows self-correction: if an observation is unexpected, the next thought can adapt.

**Limitations of vanilla ReAct:**

- Linear chain — no backtracking if a tool call fails.

- No exploration — takes the first plausible path.

- Prone to getting stuck in tool-call loops.

---

## 5. Agent Types by Autonomy

| Type | Description | Example |
|---|---|---|
| **Single-step** | One LLM call + one tool call | Simple QA with web search |
| **Multi-step (ReAct)** | Iterative reason-act-observe loop | Research agent |
| **Plan-and-execute** | First generate a full plan, then execute steps | Complex report generation |
| **Multi-agent** | Multiple specialized agents collaborating | Orchestrator + researcher + writer |
| **Autonomous (long-horizon)** | Runs for hours/days with minimal human input | Coding agent on a multi-day task |

---

## 6. Agentic vs. Non-Agentic RAG

| Dimension | Standard RAG | Agentic RAG |
|---|---|---|
| Retrieval decisions | Fixed: always retrieve | Dynamic: agent decides if/when to retrieve |
| Query strategy | Single query | Multi-query, iterative, decomposed |
| Verification | None | Agent verifies, retries if needed |
| Tool access | Only retrieval | Retrieval + search + code + APIs |
| Multi-hop | Not supported natively | Supported via iterative retrieval |

---

## 7. Production Agent Architecture

A production agent is more than a loop. It includes:

```
┌─────────────────────────────────────────────────────┐
│                    Orchestrator                       │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │
│  │  Planner │  │  Memory  │  │   Tool Registry    │ │
│  │  (LLM)   │  │ (vector  │  │  - search          │ │
│  │          │  │  store + │  │  - code_exec       │ │
│  │          │  │  episodic│  │  - db_query        │ │
│  └──────────┘  └──────────┘  │  - file_io         │ │
│                               └────────────────────┘ │
│  ┌───────────────────────────────────────────────┐   │
│  │              Guardrails Layer                  │   │
│  │  Input validation | Output filtering           │   │
│  │  Budget limits | Safety classifiers            │   │
│  └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 8. Interview Questions

**Q: What is the difference between an LLM and an LLM agent?**

A: An LLM takes a fixed input and produces a single output. An agent uses an LLM as its reasoning core but wraps it in a loop that can call external tools, observe their results, and dynamically decide the next step — repeating until the task is complete. An LLM answers "What is the weather?" in one shot; an agent calls a weather API, parses the result, and formats a response.

---

**Q: What is ReAct and why is it the dominant agent pattern?**

A: ReAct (Reason + Act) interleaves reasoning traces (*Thought*) with tool calls (*Action*) and their results (*Observation*). It's dominant because it combines the explicit reasoning benefits of chain-of-thought with the grounding benefits of tool use. The thought step prevents impulsive wrong actions; observations reduce hallucination by anchoring the model in real retrieved data.

---

**Q: How does function calling work at the API level?**

A: The caller passes a list of tool schemas (JSON with name, description, parameters) alongside the user message. If the model decides a tool call is needed, instead of generating text it emits a structured JSON object specifying the tool name and arguments. The calling framework executes the tool and appends the result as a *tool message* back to the conversation. The model then continues generating.

---

**Q: What are the risks of giving an agent access to many tools?**

A: Three main risks: (1) **Tool confusion** — overlapping tool descriptions cause wrong tool selection, compounding errors; (2) **Expanded attack surface** — more tools means more ways prompt injection or adversarial inputs can cause harmful actions; (3) **Increased latency and cost** — each tool call adds latency and token usage. Best practice: give agents the minimum tool set needed for the task (principle of least privilege).

---

**Q: What is the difference between plan-and-execute and ReAct agents?**

A: ReAct is reactive — it decides the next action at each step based on the latest observation. Plan-and-execute first generates a complete plan (all steps), then executes them sequentially or in parallel. Plan-and-execute is better for tasks with known structure; ReAct is better when the path is uncertain and depends on intermediate results.
