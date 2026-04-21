# Agent Frameworks

## 1. Why Frameworks Exist

Building an agent from scratch requires implementing the ReAct loop, tool routing, memory management, error handling, and observability. Frameworks abstract these concerns so teams can focus on task-specific logic. The main open-source frameworks as of 2025 are **LangGraph**, **CrewAI**, **AutoGen / AG2**, and **Google ADK**.

---

## 2. LangGraph

**Maintainer:** LangChain, Inc.  
**Source:** [github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)

### Core Concept

LangGraph models agent execution as a **directed graph** where:

- **Nodes** are Python functions (LLM calls, tool calls, state transforms).

- **Edges** are transitions between nodes — either unconditional or conditional (based on state).

- **State** is a typed dictionary passed between nodes; nodes read from and write to it.

```python
from langgraph.graph import StateGraph, END

def call_llm(state):
    response = llm.invoke(state["messages"])
    return {"messages": state["messages"] + [response]}

def route(state):
    if state["messages"][-1].tool_calls:
        return "tools"
    return END

graph = StateGraph(AgentState)
graph.add_node("llm", call_llm)
graph.add_node("tools", tool_executor)
graph.add_conditional_edges("llm", route)
graph.add_edge("tools", "llm")
```

### Key Features

- **Cycles:** Unlike a plain DAG, LangGraph allows cycles — the loop between the LLM node and the tools node is a natural directed cycle, enabling the ReAct loop.

- **Conditional edges:** Routing logic (e.g., "if the model called a tool, go to the tools node; otherwise return to the user") is expressed as Python functions over state.

- **Human-in-the-loop:** Interrupt points can be inserted at any node. Execution pauses and waits for external input before proceeding.

- **Streaming:** Supports token-level streaming from LLM nodes and step-level streaming of node transitions.

- **Persistence:** State can be checkpointed to a database (SQLite, Postgres) enabling long-running agents that survive crashes.

- **LangGraph Platform:** Managed deployment with built-in task queuing, scalability, and monitoring.

### When to Use LangGraph

- You need precise control over the agent's execution flow.

- Your agent has complex conditional logic or multiple interacting sub-graphs.

- You need human approval checkpoints.

- You want a statically inspectable graph that can be visualised.

### Limitations

- More verbose than higher-level frameworks.

- Requires understanding graph concepts; not ideal for quick prototyping.

- Tied to the LangChain ecosystem (though can be used standalone).

---

## 3. CrewAI

**Source:** [github.com/crewAIInc/crewAI](https://github.com/crewAIInc/crewAI)

### Core Concept

CrewAI is a **role-based multi-agent framework**. Users define a "crew" of agents, each with:

- A **role** (e.g., "Senior Research Analyst").

- A **goal** (e.g., "Find the most recent data on LLM benchmarks").

- A **backstory** (context injected into the system prompt).

- A **tool set** (what tools this agent can call).

A **Task** is a unit of work assigned to one or more agents. The **Crew** orchestrates execution — sequentially or as a hierarchical process (manager LLM routes tasks to workers).

```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(
    role="Senior Research Analyst",
    goal="Find the latest benchmarks for LLM agents",
    backstory="You are an expert in AI research...",
    tools=[search_tool, scraper_tool]
)

writer = Agent(role="Technical Writer", goal="Write a clear summary", tools=[])

task1 = Task(description="Research LLM agent benchmarks", agent=researcher)
task2 = Task(description="Write summary of findings", agent=writer)

crew = Crew(agents=[researcher, writer], tasks=[task1, task2], process=Process.sequential)
crew.kickoff()
```

### Key Features

- **Hierarchical process:** A manager agent (itself an LLM call) dynamically decides which worker agent handles each task.

- **Memory integration:** Built-in short-term (session), long-term (SQLite), entity memory, and contextual memory.

- **Training:** Crews can be trained using human feedback on task outputs (saved to a JSON file).

- **Flows:** Higher-level workflow abstraction for chaining crews and event-driven execution.

### When to Use CrewAI

- You want a quick, intuitive setup for multi-agent collaboration.

- Your use case maps naturally to roles (researcher, writer, coder, QA).

- You need built-in memory without custom implementation.

### Limitations

- Less control over execution flow than LangGraph.

- Hierarchical process delegates routing to an LLM manager, which can make unpredictable decisions.

- Less suited for complex conditional branching within a single agent.

---

## 4. AutoGen / AG2

**Original paper:** [AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation](https://arxiv.org/abs/2308.08155) (Wu et al., 2023)  
**Current name:** AG2 (rebranded October 2024 after community fork from AutoGen)  
**Note:** AG2 merged with Microsoft's Semantic Kernel in October 2025 to form a unified Microsoft agentic framework.  
**Source:** [github.com/ag2ai/ag2](https://github.com/ag2ai/ag2)

### Core Concept

AutoGen / AG2 frames multi-agent systems as **conversational interactions**. Agents are participants in a group chat; execution proceeds through message passing between agents.

```python
from autogen import AssistantAgent, UserProxyAgent

assistant = AssistantAgent("assistant", llm_config={"model": "gpt-4"})
user_proxy = UserProxyAgent("user_proxy", code_execution_config={"work_dir": "."})

user_proxy.initiate_chat(assistant, message="Write and run a Python script to sort a list.")
```

Key agent types:

- **AssistantAgent:** LLM-backed; generates text and code.

- **UserProxyAgent:** Executes code locally; acts as the "human" in the conversation.

- **GroupChat:** Routes messages between multiple agents using a GroupChatManager (itself an LLM call that decides who speaks next).

### Key Features

- **Code execution as a first-class primitive:** UserProxyAgent can run generated code, check outputs, and send results back automatically.

- **Flexible termination:** Stop on a keyword, after N turns, or when a human intervenes.

- **Swarm mode (AG2):** Dynamic handoffs — agents pass control to each other based on context, without a central manager.

- **Merged with Semantic Kernel:** As of late 2025, AG2 and Microsoft Semantic Kernel share planning and memory infrastructure.

### When to Use AG2

- Code-heavy tasks where the agent must write, run, and fix code in a loop.

- Conversational multi-agent scenarios (debate, critique-revise).

- When you want minimal framework overhead and direct message-passing control.

### Limitations

- Conversational framing can be awkward for non-conversational tasks.

- GroupChat routing (LLM-based) is non-deterministic; hard to debug.

- Integration complexity increased after merge with Semantic Kernel.

---

## 5. Google Agent Development Kit (ADK)

**Release:** April 2025  
**Source:** [google.github.io/adk-docs](https://google.github.io/adk-docs)

### Core Concept

Google ADK is designed for building **hierarchical agent trees** that deploy natively on Google Cloud (Vertex AI Agent Engine). It supports the **Agent-to-Agent (A2A) protocol** for cross-vendor agent communication.

```python
from google.adk.agents import Agent
from google.adk.tools import google_search

root_agent = Agent(
    name="orchestrator",
    model="gemini-2.0-flash",
    instruction="You are a research orchestrator.",
    tools=[google_search],
    sub_agents=[research_agent, summary_agent]
)
```

### Key Features

- **Multi-agent natively:** Sub-agents are first-class citizens in the SDK; routing is part of the agent definition.

- **A2A protocol support:** Agents expose Agent Cards (capability manifests) and communicate via the A2A standard (see `mcp_and_protocols.md`).

- **Vertex AI integration:** Native deployment on Google's managed agent infrastructure.

- **MCP compatibility:** ADK agents can consume MCP-compliant tool servers.

### When to Use ADK

- Building on Google Cloud / Vertex AI.

- Need native support for Google Workspace tools.

- Building an agent that must interoperate with agents from other vendors via A2A.

---

## 6. Framework Comparison

| Dimension | LangGraph | CrewAI | AG2 | Google ADK |
|---|---|---|---|---|
| Abstraction level | Low (graph primitives) | High (role/task/crew) | Medium (conversational) | Medium-High |
| Multi-agent | Via sub-graphs | Native (crew model) | Native (GroupChat) | Native (sub-agents) |
| State management | Explicit typed state | Built-in memory types | Message history | Managed sessions |
| Human-in-the-loop | First-class (interrupt) | Via task callbacks | Via UserProxyAgent | Supported |
| Code execution | Plugin | Plugin | First-class | Plugin |
| Deployment | Self-hosted / LangGraph Platform | Self-hosted / CrewAI+ | Self-hosted | Vertex AI |
| Protocols | MCP | MCP | MCP | MCP + A2A |
| Best for | Complex conditional flows | Role-based collaboration | Code-heavy/conversational | Google Cloud users |
