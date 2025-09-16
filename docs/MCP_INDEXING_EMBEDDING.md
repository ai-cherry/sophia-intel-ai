# Top Local MCP Servers for Indexing & Embedding (Sept 2025)

Overview
- Local‑first, open‑source MCP servers for indexing and embeddings. Optimized for IDE+CLI sharing via stdio and on‑device performance.

Recommended Servers
- mcp-local-rag (Primitive local RAG)
  - Why: Lightweight Node; MediaPipe embedder; sub‑second queries; good for code/docs.
  - Run: `node server.js --embedder mediapipe --search duckduckgo stdio`
  - Config key: `local-rag`
- Memory‑Plus MCP (Persistent embeddings)
  - Why: Rust/TS; SQLite vectors; fast, simple; cross‑session memory.
  - Run: `npx -y memory-plus-mcp stdio --db local-vectors.db --embed-model all-MiniLM-L6-v2`
  - Config key: `memory-plus`
- Vector MCP (Vector DB abstraction)
  - Why: Chroma local db or Pinecone; parallel embeds; ONNX option.
  - Run: `docker run -i -v ./vectors:/data vector-mcp:latest stdio --db chroma`
  - Config key: `vector`
- SuperIndex MCP (Framework‑aware indexing)
  - Why: Go‑based; snippet‑tailored; efficient memory usage.
  - Run: `superindex-mcp stdio --index apis --model sentence-transformers`
  - Config key: `superindex`
- Kodit MCP (Repo indexing from external sources)
  - Why: Python/Docker; caches; git integration for big repos.
  - Run: `docker run -i -v ./repos:/index kodit-mcp:latest stdio --embed onnx`
  - Config key: `kodit`

Usage
- Combine with Filesystem MCP to index files, then embed.
- Example combined config: `examples/mcp/mcp.local.json`.

Notes
- Prefer lightweight, open models (e.g., MiniLM) for CPU‑only local setups.
- Use stdio transport for zero‑latency IDE sharing and CLI orchestration.

