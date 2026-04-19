# Graph RAG — Explosive Rules 2008

A **Graph RAG** system that combines **Neo4j** (knowledge graph) + **FAISS** (vector similarity) + **Ollama** (local LLM) to accurately query the Explosive Rules 2008 PDF — including complex tables and structured data.

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start Ollama (keep running in background)
ollama serve

# 3. In a new terminal, pull models
ollama pull nomic-embed-text:latest
ollama pull gpt-oss:20b

# 4. Start Neo4j (Docker)
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password123 neo4j:latest

# 5. Test connections
python src/test_connection.py

# 6. Ingest PDF
python src/rag_pipeline.py --ingest

# 7. Launch web UI
streamlit run src/app.py
# Opens: http://localhost:8501
```

## Architecture

```
PDF (pdfplumber: text + tables)
  ↓
Semantic Chunking (section-aware)
  ↓
┌─────────────┐    ┌──────────────┐
│  FAISS Index │    │  Neo4j Graph │
│  (vectors)   │    │  (structure) │
└──────┬──────┘    └──────┬───────┘
       │                  │
       └──── Hybrid ──────┘
              Retriever
                ↓
          LLM Reranker
                ↓
          Answer Generation (Ollama)
```

## Project Structure

```
Graph_RAG/
├── src/
│   ├── app.py                # Streamlit web UI
│   ├── pdf_processor.py      # PDF parsing + table extraction (pdfplumber)
│   ├── semantic_chunker.py   # Section-aware semantic chunking
│   ├── graph_builder.py      # Neo4j graph construction & querying
│   ├── vector_store.py       # FAISS index wrapper
│   ├── hybrid_retriever.py   # Combined FAISS + Neo4j search
│   ├── reranker.py           # LLM-based relevance reranking
│   ├── rag_pipeline.py       # Main pipeline (ingest / query / CLI)
│   ├── test_connection.py    # Ollama & Neo4j connectivity tests
│   └── __init__.py
│
├── config.py                 # Loads settings from .env
├── .env                      # Credentials & parameters
├── data/
│   └── ExplosivesRules2008.pdf
├── indices/                  # FAISS index (auto-created)
├── requirements.txt
└── README.md
```

## Prerequisites

| Service | Purpose | Installation |
|---------|---------|--------------|
| **Python 3.9+** | Runtime | [python.org](https://www.python.org/downloads/) |
| **Ollama** | Local LLM & embeddings | [ollama.ai](https://ollama.ai/) |
| **Docker** (optional) | Run Neo4j in container | [docker.com](https://www.docker.com/) |
| **Neo4j** | Knowledge graph DB | Docker or [Neo4j Desktop](https://neo4j.com/download/) |

### Ollama Models (must be pulled)
```
nomic-embed-text:latest   — embeddings (768-dim)
gpt-oss:20b               — chat LLM
```

---

## Complete Setup Guide

### Step 1: Install Python Dependencies

Open **PowerShell** or **Command Prompt**, navigate to project folder:

```powershell
cd C:\Users\YourUsername\Downloads\Graph_RAG
pip install -r requirements.txt
```

**Expected output:**
```
Collecting langchain==0.1.11
...
Successfully installed langchain-0.1.11 neo4j-5.19.0 pdfplumber-0.11.0 ...
```

---

### Step 2: Start Ollama Server

**Windows:**

1. Download from [ollama.ai](https://ollama.ai/)
2. Run the installer (OllamaSetup.exe)
3. Open **PowerShell** and run:

```powershell
ollama serve
```

**Expected output:**
```
time=2026-02-26T10:30:45.123Z level=INFO msg="Ollama is running at https://localhost:11434"
```

**Keep this terminal running** (Ollama stays in background).

---

### Step 3: Pull Required Models

Open a **new PowerShell terminal** and run:

```powershell
# Pull embedding model (~600MB)
ollama pull nomic-embed-text:latest

# Pull chat model (~13GB — takes time)
ollama pull gpt-oss:20b
```

**Expected output:**
```
pulling manifest
pulling 686d6a0db3b6
...
success
```

↳ **Note**: First time can take 10-30 minutes depending on internet speed.

---

### Step 4: Start Neo4j

#### **Option A: Docker (Easiest)**

If Docker is installed:

```powershell
docker run -d --name neo4j `
  -p 7474:7474 -p 7687:7687 `
  -e NEO4J_AUTH=neo4j/password123 `
  neo4j:latest
```

**Expected output:**
```
a1b2c3d4e5f6
```

Verify it's running:
```powershell
docker ps
```

Should show `neo4j` in the list.

#### **Option B: Neo4j Desktop (GUI)**

1. Download from [neo4j.com/download/](https://neo4j.com/download/)
2. Install and launch
3. Create a new database (v5.x)
4. Set password to `password123` (or update `.env`)
5. Start the database

---

### Step 5: Configure `.env`

Create/edit `.env` in project root (`C:\...\Graph_RAG\.env`):

```env
# Ollama Configuration
OLLAMA_IP=172.17.54.24
OLLAMA_PORT=11434
EMBEDDING_MODEL=nomic-embed-text:latest
LLM_CHAT_MODEL=gpt-oss:20b

# Neo4j Configuration (update password if you changed it)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123

# File Paths
PDF_PATH=data/ExplosivesRules2008.pdf
FAISS_INDEX_DIR=indices/faiss_index

# Processing Parameters
SEMANTIC_CHUNK_THRESHOLD=1.25
RETRIEVER_TOP_K=10
RERANKER_TOP_N=5
```

---

### Step 6: Test Connections

```powershell
python src/test_connection.py
```

**Expected output:**
```
==================================================
OLLAMA  —  http://172.17.54.24:11434
==================================================
  ✓ Chat model   : gpt-oss:20b  →  OK
  ✓ Embed model  : nomic-embed-text:latest  →  dim=768

==================================================
NEO4J  —  bolt://localhost:7687
==================================================
  ✓ Connected     : user=neo4j
  ✓ Query test    : RETURN 1 → 1
  ✓ Graph nodes   : (empty, run ingestion first)

==================================================
SUMMARY
==================================================
  Ollama : ✓ OK
  Neo4j  : ✓ OK
```

If you see errors, check **Troubleshooting** section below.

---

## Usage Guide

### 📥 Step 1: Ingest the PDF

This reads `ExplosivesRules2008.pdf`, chunks it semantically, indexes it in FAISS, and builds the Neo4j graph:

```powershell
python src/rag_pipeline.py --ingest
```

**Expected output (takes 5-15 minutes first time):**
```
Loading PDF: data/ExplosivesRules2008.pdf
Extracting text and tables...
Creating semantic chunks...
Building FAISS index...
Building Neo4j graph...
✓ Ingestion complete!
  - Total chunks: 247
  - FAISS index: indices/faiss_index/
  - Neo4j nodes: 1 Document + 12 Sections + 247 Chunks + 45 Tables
```

---

### 🔍 Step 2: Query via CLI (Optional)

Test the system with a command-line query:

```powershell
python src/rag_pipeline.py --query "What is the maximum permissible limit for explosives?"
```

**Expected output:**
```
Query: What is the maximum permissible limit for explosives?

Retrieved from: FAISS (2 results) + Neo4j (3 results)
Reranking... ✓

Answer:
According to the Explosive Rules 2008, the maximum permissible limit for 
manufacture of explosives is 10,000 kg per day for Category A factories...

Sources:
  [FAISS] Page 42 - Score: 0.856
  [Neo4j] Section: Rules → Score: 0.823
```

---

### 💬 Step 3: Launch Interactive Web UI

```powershell
streamlit run src/app.py
```

**Expected output:**
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

**Browser opens automatically** to interactive chat interface.

**Features:**
- Type natural-language questions
- See AI responses with source citations
- Toggle "Show Sources" to see FAISS/Neo4j badges and relevance scores
- Toggle "Validate Answers" for answer grounding checks
- Clear chat history with button in sidebar

---

## Common Commands Reference

| Task | Command |
|------|---------|
| **Test connections** | `python src/test_connection.py` |
| **Ingest PDF** | `python src/rag_pipeline.py --ingest` |
| **CLI query** | `python src/rag_pipeline.py --query "Your question"` |
| **Web UI** | `streamlit run src/app.py` |
| **Check Ollama** | `ollama list` |
| **Neo4j browser** | http://localhost:7474 (if using Docker) |
| **Restart Neo4j** | `docker restart neo4j` |
| **Stop Neo4j** | `docker stop neo4j` |
| **Clear FAISS index** | `rm -r indices/faiss_index` (then re-ingest) |
| **Clear Neo4j graph** | Access Neo4j browser → Run `MATCH (n) DELETE n` |

---

## How RAG Works

```
User: "What are the safety rules?"
    ↓
[Hybrid Retrieval]
  • FAISS: Vector similarity search → top 5 chunks
  • Neo4j: Fulltext + graph traversal → top 5 chunks
  • Deduplicate & merge scores
    ↓
[Reranker]
  • LLM scores each chunk for relevance (0-10)
  • Keeps top 5 most relevant
    ↓
[Answer Generation]
  • Feeds chunks + question to LLM
  • LLM generates grounded answer
  • Optional validation check
    ↓
User: [Answer with sources]
```

---

## Troubleshooting

### Ollama Issues

**Error: `Connection refused`**
```
XConnecting to Ollama at http://172.17.54.24:11434
✗ Connection failed: [Errno 111] Connection refused
```
**Solution:**
- Ensure Ollama is running: `ollama serve`
- Check `OLLAMA_IP` in `.env` (should be `172.17.54.24` or `localhost`)
- Test manually: `curl http://172.17.54.24:11434/api/tags`

**Error: `Model not found`**
```
❌ Model 'gpt-oss:20b' not found
```
**Solution:**
```powershell
ollama list  # see installed models
ollama pull gpt-oss:20b  # install if missing
ollama pull nomic-embed-text:latest
```

### Neo4j Issues

**Error: `Cannot connect to bolt://localhost:7687`**

**Solution:**
- Check Neo4j is running: `docker ps` (should show `neo4j`)
- Restart: `docker restart neo4j`
- Verify password in `.env` matches what you set
- If using Neo4j Desktop, make sure database is started

**Error: `CONSTRAINT_ERROR with existing data`**

**Solution:** Clear the graph and re-ingest:
```powershell
# Access Neo4j browser: http://localhost:7474
# Login with neo4j / password123
# Run in browser: MATCH (n) DETACH DELETE n
# Then re-ingest: python src/rag_pipeline.py --ingest
```

### PDF Processing Issues

**Error: `FileNotFoundError: data/ExplosivesRules2008.pdf`**

**Solution:**
- Verify file exists: `ls data/`
- Update `PDF_PATH` in `.env` if filename is different

**Error: `Zero chunks created (PDF too small?)`**

**Solution:**
- PDF might have only images (no text)
- Try with test PDF first
- Check `SEMANTIC_CHUNK_THRESHOLD` in `.env` (lower = more chunks)

### Performance Issues

**Slow ingestion (>30 minutes)**
- Normal for first run (Ollama generates embeddings)
- Subsequent queries will be fast (FAISS cached)
- Check Ollama isn't other processes: `ollama list`

**Streamlit UI is slow**
- Reranking step takes time (configurable in `.env`)
- Increase `RERANKER_TOP_N` for faster but less accurate answers

**OutOfMemory error**
- Reduce `RETRIEVER_TOP_K` in `.env` (default: 10)
- Close other applications

---

## How Modules Work Together

### `pdf_processor.py` → Extract & Structure
```
PDF file
  → Read pages with pdfplumber
  → Extract tables (as markdown)
  → Extract text
  → Detect headers (CHAPTER, RULE, etc.)
  → Output: List of Document objects (text + metadata)
```

### `semantic_chunker.py` → Split Semantically
```
Documents
  → Split by section boundaries (CHAPTER, PART, etc.)
  → Apply LangChain SemanticChunker per section
  → Keep table chunks intact (no further splitting)
  → Output: List of Chunks with metadata
```

### `vector_store.py` → FAISS Indexing
```
Chunks
  → Get embeddings via Ollama (nomic-embed-text)
  → Build FAISS index
  → Save to indices/faiss_index/
  → Output: Searchable vector store
```

### `graph_builder.py` → Neo4j Graph
```
Chunks
  → Create nodes: Document, Section, Chunk, Table
  → Create relationships: HAS_SECTION, CONTAINS, NEXT_CHUNK
  → Create fulltext index on chunk content
  → Output: Queryable Neo4j graph
```

### `hybrid_retriever.py` → Combined Search
```
User query
  → FAISS: Vector similarity (top 5)
  → Neo4j: Fulltext + graph traversal (top 5)
  → Merge results (deduplicate)
  → Output: Combined ranked list
```

### `reranker.py` → LLM Validation
```
Retrieved chunks
  → Score each with LLM (0-10 relevance)
  → Combine: 40% retrieval + 60% rerank scores
  → Keep top N (default: 5)
  → Output: Final ranked chunks
```

### `rag_pipeline.py` → Orchestration
```
PDF Ingestion:
  pdf_processor → semantic_chunker → vector_store + graph_builder

Query:
  user query → hybrid_retriever → reranker → Ollama LLM → answer
```

### `app.py` → Web Interface
```
Streamlit UI
  → Chat input
  → Call rag_pipeline.query()
  → Display answer + sources + scores
  → Show source badges (FAISS vs Neo4j)
```

---

## Module Reference

| File | Class/Function | What It Does |
|------|----------------|-------------|
| `pdf_processor.py` | `process_pdf()` | Parse PDF, extract tables & text |
| `pdf_processor.py` | `build_combined_documents()` | Group text+tables per page + standalone tables |
| `semantic_chunker.py` | `semantic_chunk_documents()` | Split by sections, apply semantic chunking |
| `vector_store.py` | `VectorStore` class | FAISS index wrapper (create, load, search) |
| `graph_builder.py` | `GraphBuilder` class | Create Neo4j nodes, edges, fulltext index |
| `graph_builder.py` | `get_graph_context()` | Query graph (fulltext + neighbors + tables) |
| `hybrid_retriever.py` | `HybridRetriever` class | Combine FAISS + Neo4j search, deduplicate |
| `reranker.py` | `Reranker` class | LLM-based relevance scoring |
| `rag_pipeline.py` | `GraphRAGPipeline` class | Main orchestrator (ingest + query) |
| `app.py` | Streamlit app | Web chatbot interface |
| `test_connection.py` | `test_ollama()` | Verify Ollama connectivity |
| `test_connection.py` | `test_neo4j()` | Verify Neo4j connectivity |

---

## Architecture & Design Decisions

### Why This Stack?

| Component | Why Chosen | Alternatives |
|-----------|-----------|--------------|
| **Ollama** | Local, no APIs, full privacy | GPT-4, Claude (cloud) |
| **Neo4j** | Structured knowledge graphs, fast queries | MongoDB, Elasticsearch |
| **FAISS** | Fast vector similarity, no server needed | Pinecone, Weaviate (cloud) |
| **pdfplumber** | Accurate table extraction | PyPDF, pdfminer (simpler but less accurate) |
| **SemanticChunker** | Preserves meaning boundaries | Fixed-size chunking (naive) |
| **LLM reranking** | Validates relevance before generating | Use only FAISS (less accurate) |

### Why Hybrid Search?

- **FAISS alone**: Fast but sometimes misses structured data
- **Neo4j alone**: Great for structure but weak on semantic similarity
- **Hybrid**: Best of both worlds — vectors + structure + graph traversal

### Why Standalone Table Docs?

Tables can be hard to retrieve with just vector similarity. By creating standalone "Table: [table_name]" documents, they're discoverable even for vague queries like "show me numbers" or "what are the fees?"

---

## Example Queries to Try

```
"What is the maximum quantity of explosives per magazine?"
"Show me all safety requirements"
"What are the licensing rules?"
"How should detonators be stored?"
"What is the penalty for violations?"
"List all regulatory authorities"
```
