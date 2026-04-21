## 1. Overview

Chunking splits documents into smaller units before embedding and indexing. It is a critical design choice because it directly determines retrieval granularity, context relevance, latency, and cost. Poor chunking is one of the easiest ways to silently break a RAG system.

---

---

## 2 Why Chunks Must Be Sized Carefully

Embedding models have fixed input limits (typically 512 to 8192 tokens), so documents must be split. But chunk size affects quality in both directions:

- **Too small:** Chunks lose semantic meaning; retrieval returns fragments that don't fully answer the question.

- **Too large:** Chunks contain multiple unrelated topics; embedding quality degrades; context window fills with noise.

---

---

## 3. Chunking Strategies

### Fixed-Size Chunking

Documents are split into consecutive windows of N tokens with optional overlap. Simple and fast, but ignores semantic boundaries.

**Algorithm:**

1. Tokenise the document.

2. Split into consecutive windows of size N.

3. Optionally overlap adjacent windows by M tokens.

- **Pros:** Simple to implement; fast and scalable; good baseline.

- **Cons:** Ignores semantic boundaries; may split sentences mid-thought.

- **Use when:** Baseline systems; uniform document formats; large-scale indexing where simplicity matters.

---

### Sentence-Based Chunking

Documents are split at sentence boundaries, accumulating sentences until a token threshold is reached.

- **Pros:** Preserves sentence semantics; reduces mid-sentence splits.

- **Cons:** Sentence lengths vary; ignores higher-level document structure.

- **Use when:** Narrative text; QA over articles or reports.

---

### Paragraph-Based Chunking

Chunks are formed at paragraph boundaries and merged if small; large paragraphs are split further if needed.

- **Pros:** Preserves local topical coherence; aligns with human-written structure.

- **Cons:** Paragraph length is highly inconsistent; formatting noise can affect quality.

- **Use when:** Well-structured documentation; markdown or HTML content.

---

### Recursive Chunking

Applies a hierarchy of split rules — sections → paragraphs → sentences → fixed-size fallback — only falling back to finer splits when the chunk exceeds the size limit.

- **Pros:** Preserves document structure; produces semantically meaningful chunks; handles diverse formats.

- **Cons:** More complex to implement; requires reliable document parsing.

- **Use when:** Enterprise documents; PDFs with headings; mixed-format content. **This is the most common production approach.**

---

### Semantic / Context-Aware Chunking

Adjacent text units are grouped based on embedding similarity rather than fixed boundaries.

- **Pros:** High semantic coherence; reduces context fragmentation.

- **Cons:** Computationally expensive — requires embedding during preprocessing; sensitive to similarity thresholds.

- **Use when:** High-precision RAG; smaller corpora where quality matters most.

---

### Proposition-Based Chunking

Use an LLM to extract atomic factual propositions from each paragraph, storing each as a micro-chunk. Example: a paragraph about a company becomes individual chunks like "Founded in 2010", "Headquartered in Berlin", "Has 500 employees."

- **Pros:** Maximum semantic precision; each chunk answers exactly one question; retrieval is very accurate.

- **Cons:** LLM inference required at index time (expensive); chunks lose surrounding narrative context.

- **Use when:** High-precision QA over structured factual content; small corpora where index build cost is acceptable.

---

### Late Chunking

(Jina AI, 2024) Embed the full document first using a long-context encoder, then chunk the resulting **token embeddings** rather than the raw text. Each chunk's embeddings carry context from the surrounding document.

- **Pros:** Chunks retain cross-chunk context; resolves co-reference ("it", "the company") within chunks; better retrieval for narrative documents.

- **Cons:** Requires a long-context embedding model; cannot be applied to corpora already indexed with standard chunking.

- **Use when:** Documents where context from earlier/later paragraphs is needed to interpret individual chunks (legal contracts, research papers, long-form articles).

---

### Sliding Window Chunking

Overlapping windows slide across the document (e.g., 512-token window, 256-token stride).

- **Pros:** Preserves cross-boundary context; reduces information loss at chunk edges.

- **Cons:** Doubles or more the index size; higher storage and retrieval cost; redundant embeddings.

- **Use when:** Long-form documents; multi-hop reasoning tasks; cases where boundary loss is critical.

---

---

## 4 Chunk Size and Top-k Are Coupled

Changing chunk size almost always requires adjusting top-k. **They must be tuned jointly.**

| Chunk Size | Typical Top-k | Behaviour |
|---|---|---|
| Small (100–300 tokens) | High (10–20) | High recall, lower precision — many fragments retrieved |
| Medium (300–700 tokens) | Medium (4–8) | Balanced — good default starting point |
| Large (700–1500 tokens) | Low (1–3) | High precision, risk of missing relevant info |

**Common failure patterns:**

- Small chunks + low top-k → missing required information

- Large chunks + high top-k → context overload and noise

- Large chunks + low top-k → partial coverage

---

---

## 5 Chunk Overlap

Overlap (sharing tokens between adjacent chunks) prevents information loss at chunk boundaries.

**Typical settings:**

- Fixed-size chunking: 10–20% overlap

- Sliding window: stride equals 50% of window size

- Recursive chunking: overlap often unnecessary

**Benefits:** Improved recall; reduced boundary effects.

**Costs:** Larger index; higher storage and retrieval cost; redundant embeddings.

> Overlap is a mitigation strategy, not a substitute for good chunking design.

---

---

## 6 Chunk Metadata and Filtering

Attaching structured metadata to each chunk enables filtering before or after similarity search — one of the highest-ROI improvements in a vanilla RAG system.

**Common metadata fields:** document ID, section heading, timestamp/version, author, content type, access permissions.

**How it's used:**

- Pre-filter by document type, date, or access permission before ANN search (faster, but risks reducing recall if over-filtered).

- Post-filter after ANN search (preserves recall, wastes compute on irrelevant candidates).

**Example:** Retrieve only chunks from documents created after a certain date, or from a specific product version.

---

---

## 7 Special Cases: Tables and Code

Text-centric chunking destroys the structure of tables and source code.

**Tables:**

- Never split a table row across chunks.

- Attach the table schema and column headers as metadata to every row-chunk.

- Consider serialising rows to natural language for embedding.

**Code:**

- Chunk at function or class boundaries — never split a function across chunks.

- File-level chunking for small files is acceptable.

- Long-range dependencies mean that smaller granularity (line-level) loses context.

---

---

## 8 Adaptive Chunking

Different queries require different granularity. A single static chunking strategy cannot optimally serve all query types.

| Query Type | Preferred Chunking |
|---|---|
| Fact lookup | Small chunks |
| Concept explanation | Medium chunks |
| Procedural steps | Large chunks |
| Multi-hop reasoning | Overlapping or sliding window |

**Adaptive approach:** Maintain multiple indexes with different chunk sizes and select based on query classification. Higher accuracy, but more system complexity.

---
