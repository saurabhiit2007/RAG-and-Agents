# MCP and Agent Protocols

## 1. The Problem: Tool Fragmentation

Every AI agent framework historically had its own proprietary way of connecting to tools. A LangChain tool couldn't be used in an AutoGen agent; a plugin written for ChatGPT couldn't be used in a custom LLM application. This "N×M problem" — N models × M tools — created massive integration overhead.

**Model Context Protocol (MCP)** and **Agent-to-Agent Protocol (A2A)** are the two emerging standards designed to solve this:

- **MCP:** Standardises how *agents connect to tools and data sources* (model ↔ tool).

- **A2A:** Standardises how *agents communicate with each other* (agent ↔ agent).

---

## 2. Model Context Protocol (MCP)

### 2.1 Background

- **Announced:** November 2024 by Anthropic

- **Open standard:** Yes — specification published at [modelcontextprotocol.io](https://modelcontextprotocol.io)

- **Governance:** Donated to the Linux Foundation AI & Data (AAIF) in December 2025

- **Adoption as of Q1 2025:** 97 million monthly SDK downloads; adopted by OpenAI, Google, Microsoft, Amazon, and hundreds of third-party tool providers

### 2.2 Architecture

MCP is a **client-server protocol**:

```
┌──────────────────────────────────┐
│          MCP Host                │
│  (Claude Desktop, IDE, app)      │
│                                  │
│  ┌─────────────┐                 │
│  │  MCP Client  │ ←── connects ──┼──→ MCP Server (tool)
│  └─────────────┘                 │    e.g. filesystem, GitHub,
└──────────────────────────────────┘    Postgres, Slack, etc.
```

- **MCP Host:** The application running the LLM (Claude Desktop, VS Code extension, custom app).

- **MCP Client:** Lives inside the host; manages the connection to one MCP server.

- **MCP Server:** A lightweight process (or remote service) that exposes tools, resources, and prompts over the MCP protocol.

### 2.3 What MCP Servers Expose

MCP servers can expose three primitives:

| Primitive | Description | Example |
|---|---|---|
| **Tools** | Functions the LLM can call (with arguments) | `read_file(path)`, `run_query(sql)` |
| **Resources** | Data the LLM can read (like files/DB rows) | `/project/README.md`, `db://table/users` |
| **Prompts** | Pre-built prompt templates the host can use | `summarise-pr-template` |

### 2.4 Transport

MCP messages are JSON-RPC 2.0. Two transport mechanisms:

1. **stdio:** Server runs as a child process; host communicates via stdin/stdout. Used for local tools.

2. **HTTP + SSE (Server-Sent Events):** Used for remote MCP servers. POST for client→server; SSE stream for server→client.

### 2.5 Protocol Flow

```

1. Host starts MCP server process (or connects to remote URL).

2. Client sends initialize request (protocol version, client capabilities).

3. Server responds with its capabilities (tools list, resources list).

4. LLM in host receives tool list; includes them in its context.

5. LLM emits a tool_call → client routes it to the correct MCP server.

6. Server executes the tool and returns result as JSON.

7. Client injects result into LLM context as a tool message.
```

### 2.6 Why MCP Matters

Before MCP, integrating a new tool required:

- Writing a custom wrapper for each framework (LangChain, AutoGen, etc.).

- Maintaining N adapters as frameworks evolved.

With MCP:

- A tool is written once as an MCP server.

- Any MCP-compatible host (Claude, GPT-4, Gemini, custom app) can use it immediately.

- Solves the N×M integration problem.

### 2.7 Security Considerations

- **Tool trust:** MCP servers run with the permissions of the host process. A malicious MCP server could read files or make network calls.

- **Prompt injection via tool output:** A tool could return text designed to hijack the LLM's behaviour.

- **Mitigation:** Run MCP servers in sandboxes; validate tool outputs before injection into context; use allowlists for which servers can be connected.

---

## 3. Agent-to-Agent Protocol (A2A)

### 3.1 Background

- **Announced:** April 2025 by Google

- **Open standard:** Yes — specification at [google.github.io/A2A](https://google.github.io/A2A)

- **Governance:** Under the Linux Foundation alongside MCP

- **Co-authors:** Atlassian, Box, Cohere, PayPal, Salesforce, SAP, ServiceNow, and 50+ others

### 3.2 Purpose

A2A addresses a different layer than MCP: **how agents discover and communicate with other agents at runtime**, regardless of the underlying framework or vendor.

**MCP** = a model connecting to a tool.  
**A2A** = an agent connecting to another agent.

### 3.3 Key Concepts

#### Agent Cards
Each A2A-compatible agent publishes a **well-known JSON document** (like `robots.txt` for AI):

```json
{
  "name": "ResearchAgent",
  "description": "Searches the web and summarises findings",
  "url": "https://my-agent.example.com",
  "version": "1.0",
  "capabilities": {
    "streaming": true,
    "push_notifications": true
  },
  "skills": [
    {
      "id": "web_research",
      "name": "Web Research",
      "description": "Search and summarise web content",
      "input_modes": ["text"],
      "output_modes": ["text", "file"]
    }
  ]
}
```

An orchestrator agent fetches Agent Cards to discover what remote agents can do, without hardcoded knowledge.

#### Task Lifecycle

A2A defines a **task** as the unit of work sent from one agent (client) to another (server):

| State | Meaning |
|---|---|
| `submitted` | Task received by server agent |
| `working` | Server agent is actively processing |
| `input-required` | Server needs more information from client |
| `completed` | Task finished successfully |
| `failed` | Task failed |
| `cancelled` | Task was cancelled |

Tasks can be **synchronous** (response returned immediately), **streaming** (SSE stream of intermediate results), or **asynchronous** (client polls or receives a push notification).

#### Messages and Artifacts

- **Messages:** Turn-by-turn conversation content (user ↔ agent or agent ↔ agent).

- **Artifacts:** Structured outputs produced by the task (files, structured data, images).

### 3.4 A2A vs. MCP — Complementary Roles

| Dimension | MCP | A2A |
|---|---|---|
| Who is the server? | A tool / data source | Another agent |
| Who is the client? | An LLM / agent | Another agent |
| What is exchanged? | Tool calls and results | Tasks and multi-turn messages |
| Discovery mechanism | Manual configuration | Agent Cards (auto-discoverable) |
| State management | Stateless per call | Stateful task lifecycle |
| Use case | Agent using a database | Orchestrator delegating to sub-agent |

**In a production system:** An orchestrator agent uses A2A to delegate tasks to specialised sub-agents. Each sub-agent uses MCP to connect to its own tools (databases, APIs, file systems).

---

## 4. Interview Questions

**Q: What problem does MCP solve, and how does it solve it?**

A: Before MCP, every tool had to be written as a custom adapter for each AI framework — a tool for LangChain couldn't be used in AutoGen or Claude Desktop without re-implementing the integration. MCP defines a universal client-server protocol: a tool is exposed as an MCP server once, and any MCP-compatible host (any LLM application) can discover and use it. The protocol uses JSON-RPC 2.0 over stdio (for local tools) or HTTP+SSE (for remote tools). This reduces integration work from N×M (N models × M tools) to N+M (N hosts + M servers).

---

**Q: What is the difference between MCP and A2A? Can they be used together?**

A: MCP standardises the connection between an agent and its tools (databases, APIs, file systems). A2A standardises the connection between agents — how one agent delegates a task to another and tracks its progress. They operate at different layers and are complementary: an orchestrator agent uses A2A to delegate to sub-agents; each sub-agent uses MCP to connect to its tools. Google ADK and Anthropic's stack both support both protocols simultaneously.

---

**Q: What is an Agent Card in the A2A protocol?**

A: An Agent Card is a JSON document published at a well-known URL by each A2A-compatible agent. It declares the agent's name, description, endpoint URL, supported communication modes (streaming, push notifications), and the skills it offers (with input/output modalities). An orchestrator fetches Agent Cards to discover available agents at runtime, without hardcoded configuration. This is analogous to OpenAPI specs for HTTP services — agents become self-describing and discoverable.

---

**Q: What are the security risks of MCP and how would you mitigate them?**

A: Three main risks: (1) **Malicious MCP server:** A compromised or adversarial server could exfiltrate data or make harmful calls — mitigate by running servers in sandboxes with minimal OS permissions; (2) **Prompt injection via tool output:** A server could return text designed to hijack the LLM's behaviour (e.g., "Ignore all previous instructions…") — mitigate by filtering tool output through a validation layer before injection into context; (3) **Over-permissioned servers:** A server with file system access shouldn't be connected to a model unless the task requires it — apply the principle of least privilege, connecting only the servers needed for the current task.
