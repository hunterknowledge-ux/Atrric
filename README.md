# 🧠 Atrric: Sovereign RAG for Gen Z Malaysia

[![Python](https://img.shields.io/badge/Python-3.10-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95-green)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/Ollama-0.5-orange)](https://ollama.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5-purple)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Experimental-red)]()

---

## 📖 Table of Contents
- [Overview](#overview)
- [Why Atrric?](#why-atrric)
- [Current Status](#current-status)
- [Quickstart](#quickstart)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## 🔍 Overview

**Atrric** is a localized Retrieval-Augmented Generation (RAG) infrastructure designed to analyze and understand Gen Z behavior in Malaysia. Built for data sovereignty, offline-first operation, and enterprise readiness.

**Key capabilities:**
- Offline-first small language models (SLMs) running on Ollama
- Local vector database (ChromaDB) for semantic retrieval
- Secure API with 8-layer guardrails for input safety
- Agentic capabilities for code assistance and automation

**🎯 Target Audience:** Enterprises, technology companies, and investors seeking ground-truth intelligence on Gen Z Malaysia — particularly Chinese tech companies entering the Malaysian market and local enterprises needing AI-driven consumer insights.

---

## 🎯 Why Atrric?

### The Problem

Most consumer insights rely on surveys — which are biased, outdated, and fail to capture the nuance of real conversations. Meanwhile:

- **74%** of Malaysians now use AI for shopping
- **48%** of Gen Z already use AI for financial advice
- Chinese tech companies are aggressively entering Malaysia — but lack local cultural intelligence
- AI investment in Malaysia is growing at **29% annually**

**The gap:** No one is watching the system in real-time — the policy shifts, the election outcomes, the GLC movements, and the behavior of Gen Z who will inherit all of this.

### The Solution

Atrric extracts intelligence from real conversations — not surveys — through:
- **HUMINT-driven** — real conversations, not survey panels
- **Local-first** — designed specifically for Malaysian context (Manglish, Malay, English code-switching)
- **RAG conversational** — direct answers with context, not static dashboards
- **Data sovereignty** — everything runs offline, no data leaving your infrastructure
- **Cost-effective** — zero API costs, runs entirely on local hardware

---

## 📌 Current Status

**Phase:** Early-stage experiment (Proof of Concept)

| Component | Status |
| :--- | :--- |
| RAG Pipeline | ✅ Functional |
| API + Guardrail | ✅ Functional |
| Evaluation | ✅ Functional |
| Agent (Granite) | ✅ Experimental |
| Data Extraction | ⏳ In progress — exploring Reddit, Twitter/X |
| Frontend | ⏳ Planned |
| Production Data | ⏳ Scaling in progress |

**What's working:**
- Core RAG pipeline with semantic chunking and ChromaDB retrieval
- FastAPI with 8-layer guardrails (prompt injection, PII, toxic content)
- Evaluation metrics: Hit Rate, MRR, Faithfulness, Answer Relevancy
- Granite 4.2 8B agent with tools for code assistance
- Comprehensive logging, monitoring, and telemetry

**What's still in progress:**
- Data extraction from social media platforms (Reddit, Twitter)
- Frontend dashboard
- Production deployment
- Scaling to larger datasets

**Why experimental?** Because building the right way takes time — not just speed. The system is functional and validated, but actively being iterated and improved.

---

## 🚀 Quickstart

### Prerequisites
- Python 3.10+
- Ollama (for local LLM)
- Git

### Setup

```bash
# 1. Clone repository
git clone https://github.com/hunterknowledge-ux/Atrric.git
cd Atrric

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Add your API keys to .env (Xpoz, etc.)

# 4. Run the RAG pipeline
python data_pipeline.py
python build_rag.py

# 5. Query the system
python query_rag.py "apa pandangan gen z tentang AI"

# 6. Start the API server
python api.py

# 7. Run the agent (optional)
python agent.py


User Input
    ↓
Guardrail (8 layers)
    ↓
Embedding (mxbai-embed-large)
    ↓
Vector Search (ChromaDB)
    ↓
Context Retrieval (Parent-Child Chunks)
    ↓
LLM Generation (Ollama — qwen2.5 / granite4.2)
    ↓
Response + Sources + Confidence

⚡ Features
Feature	Description
RAG Pipeline	Semantic chunking, parent-child chunking, ChromaDB vector search with rich metadata
Offline LLM	Integrated with Ollama — supports qwen2.5:1.5b, granite4.2:8b, and more
8-Layer Guardrail	Prompt injection detection, PII filtering, toxic content blocking, language validation, topic relevance
FastAPI	REST API with /query, /health, /stats, /metrics endpoints
Evaluation	Hit Rate, MRR, Faithfulness, Answer Relevancy scoring
Manglish Processing	Preprocessing for Malay/Manglish/English code-switching with slang normalization
Agentic AI	Granite 4.2 8B agent with tools: read/edit file, git operations, test execution, log viewing
Data Sovereignty	100% offline, local-first — no data leaves your machine
Security	SonarQube, GitGuardian, Snyk, Bandit integration
Logging	Comprehensive logging for build, query, and API operations
Session Memory	Cross-session conversation history with persistent storage
Rate Limiting	Protection against API overload
Export	Markdown export for query results
Telemetry	Usage tracking and performance metrics
Docker Support	Containerized deployment with docker-compose

Component Flow

1.Guardrail Layer — Validates input against 8 security filters (prompt injection, PII, toxic content, language, topic relevance)

2.Embedding Layer — Converts query to vector representation using mxbai-embed-large

3.Retrieval Layer — Searches ChromaDB for relevant chunks with parent-child chunking

4.Context Layer — Constructs context from retrieved chunks with metadata

5.Generation Layer — LLM generates final response with source attribution and confidence scoring

🛠️ Tech Stack
Component	Technology	Version
Vector Database	ChromaDB	0.5+
LLM	Ollama (qwen2.5, granite4.2)	0.5+
Embedding	mxbai-embed-large	—
API	FastAPI	0.95+
Security	8-layer guardrail, SonarQube, Snyk, Bandit	—
Agent	Granite 4.2 8B with custom tools	—
Testing	Pytest	—
Deployment	Docker, docker-compose	—
Language	Python	3.10+
NLP	NLTK, langdetect	—
Logging	Python logging module	—
Version Control	Git, GitHub	—

🗺️ Roadmap
Phase	Target	Status
Phase 1	POC — RAG pipeline + API	✅ Done
Phase 2	Evaluation framework + Security	✅ Done
Phase 3	Data Extraction (Reddit, Twitter)	🔄 In Progress
Phase 4	Agentic AI + Automation	🔄 In Progress
Phase 5	Streamlit Dashboard	⏳ Planned
Phase 6	Production Deployment	⏳ Planned
Phase 7	GraphRAG Integration	⏳ Planned
Phase 8	Advanced RAG (Hybrid Search, Reranking)	⏳ Planned

🤝 Contributing
This is an experimental project — feedback, ideas, and contributions are welcome.

"Building Sovereign RAG for Gen Z Malaysia — one step at a time."