
# ATRRIC

**Sovereign RAG & Market Intelligence Engine for Malaysian Gen Z.**

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.110%2B-green)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/chromadb-0.5%2B-purple)](https://www.trychroma.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Status: Early Development](https://img.shields.io/badge/status-early%20development-red)]()

---

## Table of Contents

- [What is ATRRIC](#what-is-atrric)
- [The Problem](#the-problem)
- [The Approach](#the-approach)
- [Use Cases](#use-cases)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Status](#project-status)
- [Quickstart](#quickstart)
- [Roadmap](#roadmap)
- [Non-Goals](#non-goals)
- [Contributing](#contributing)
- [License](#license)

---

## What is ATRRIC

ATRRIC is a retrieval-augmented generation (RAG) engine and automated report generator built for analyzing Gen Z behavior and local market dynamics in Malaysia. It is designed for data sovereignty, offline-capable operation, and flexible deployment.

The system ingests real conversation data, builds a semantic index, answers business queries with source attribution, and generates full B2B-grade market intelligence reports (HTML/Markdown).

---

## The Problem

Consumer intelligence in Malaysia has three structural weaknesses:

1. **Survey bias.** Most insights come from panels that self-select, skew urban and English-speaking, and miss how Gen Z actually talks and thinks.
2. **Data sovereignty gap.** Existing AI analytics tools route data to foreign servers. Enterprises with sensitive data have no compliant option.
3. **No real-time signal.** Policy shifts, economic pressure, and platform migration happen weekly. Quarterly reports cannot keep up.

---

## The Approach

ATRRIC addresses these by design:

- **Real conversation data.** Ingests qualitative data from real discussions (social media, forums), not survey responses.
- **Flexible LLM backend.** Choose between local inference (full sovereignty) or API providers (like ILMU API) for lower hardware requirements.
- **Multilingual by default.** Handles Malay, English, and Manglish code-switching natively.
- **Reasoning transparency.** Every answer includes source attribution and confidence scoring.
- **Bring your own model.** No vendor lock-in. Configure any compatible LLM.

---

## Use Cases

- Market research on Gen Z consumer behavior in Malaysia
- Enterprise deployment requiring local data sovereignty
- Academic research on regional language models and RAG systems
- Rapid prototyping of domain-specific RAG pipelines
- Automated generation of B2B market intelligence reports

---

## Architecture

```text
[Extract] -> [Process (Analytics)] -> [Generate (RAG + LLM)] -> [Report (HTML/MD)]
              |
         (SQLite / ChromaDB / Local Bedrock)

User Query -> Guardrails -> Embedding -> Retrieval -> Context Assembly -> Generation -> Response
```

Project Structure

```text
Atrric/
├── config.py                # single source of truth
├── build_rag_phone.py       # RAG builder (Mobile focus)
├── sqlite_ingest.py         # Local database ingestion
├── sqlite_query.py          # Local database querying
├── yt_convert.py            # YouTube data converter
├── pocket_vector_bedrock.py # Vector embedding (Archive/Laptop)
├── analytics/               # NLP extraction, sentiment, entity discovery
├── analytics_out/           # JSONL data & summary
├── archive/                 # Laptop setup (ChromaDB, Local Inference) - INCOMPLETE
├── assets/                  # README screenshots
├── core/                    # LLM wrappers, Router, RAG engine, OmniFuse
├── data/                    # Data pipeline scripts
├── frontend/                # Browser UI (server.py)
├── logs/                    # Execution logs
├── raw_data/                # Raw scraped text files
├── report/                  # Report Layer (loader, picker, generate, template)
└── scripts/                 # Utility scripts
```

Design Principles

· Backend-agnostic. Switch between local inference, API, and SQLite/Chroma via configuration.
· Two-layer chunking. Child chunks for precise retrieval, parent chunks for full context. Prevents the classic RAG trade-off between precision and coherence.
· Rich metadata. Every chunk carries source file, hash, timestamp, chunk type, and parent index for traceability.
· Modular Pipeline. Ingestion, retrieval, generation, and report rendering are separate components.

---

Tech Stack

Layer Technology
Vector Database ChromaDB / SQLite / Pocket Vector
LLM Backend ILMU API (Current) / Ollama (Planned)
Embedding Backend Pluggable: local or API
API Framework FastAPI (frontend/server.py)
Language Python 3.10+
NLP NLTK, langdetect
Testing pytest
Containerization Docker, docker-compose

---

Project Status

Current phase: Early development.

The architecture is complete. Core components are implemented. End-to-end verification is in progress.

Component Status
Analytics & Extraction Pipeline Implemented
Report Generation (HTML/MD) Implemented
SQLite/Phone RAG Implemented
Parent-child chunking Implemented
ChromaDB retrieval Implemented (Archive)
Guardrails (6-layer) Implemented
FastAPI endpoints Implemented
Flexible backend abstraction In progress
Evaluation framework In progress
Local Inference (Laptop) Incomplete / Untested

Known Limitations

· The local heavy-lifting setup (ChromaDB embedding, local inference) on the laptop is currently incomplete and has not been rigorously tested. The folder archive/ contains the legacy setup.
· The active pipeline currently relies on API-based LLM calls (ILMU) and mobile execution (Termux) using SQLite/pocket vectors.
· Evaluation metrics are defined but not yet benchmarked against ground truth.
· Data extraction requires an Xpoz API key for social media sources.
· Test coverage is minimal.

Limitations are published openly so contributors and users can calibrate expectations accurately.

---

Verified Deployments & Hybrid Workflow

Development Strategy: The initial heavy-lifting setup (local ChromaDB, local model inference) was started on a laptop but remains incomplete. Daily iteration, analytics processing, API routing, and report generation are done entirely on a mobile device (boarding school workflow).

Environment Hardware Model Status
Android / Termux Samsung A10s, 2GB RAM, ARMv7 (32-bit) SmolLM2 135M + hourai2-50m embedding Proof of concept
Laptop (Archive) Standard PC ChromaDB + Local LLM Incomplete

llama.cpp compiled from source for ARMv7:

assets/screenshot-hardware.png

Embedding and vector search working on-device:

assets/screenshot-embedding.png

Notes on the phone deployment:

· llama.cpp was compiled from source (Clang 21.1.8, ARMv7 target) due to lack of official ARMv7 binaries.
· Embedding runs at 128 dimensions via hourai2-50m-embedding.
· Generation runs at ~2.5 tokens/second via SmolLM2 135M on a MediaTek Helio P22 CPU.
· Output quality is limited by the 135M parameter model. The pipeline architecture itself is sound and works end-to-end.
· Production deployments should target 1B–8B parameter models on machines with 8GB+ RAM.

---

Quickstart

Prerequisites

· Python 3.10 or higher
· Git
· ILMU API Key (or other API provider key)

Setup

```bash
# 1. Clone the repository
git clone https://github.com/hunterknowledge-ux/Atrric.git
cd Atrric

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env: choose backend and provide credentials

# 4. Ingest Data (SQLite)
python sqlite_ingest.py

# 5. Run a query test
python sqlite_query.py "how does Gen Z view AI in Malaysia"

# 6. Generate B2B Report
python -m report --yes

# 7. Start the Frontend Server
python frontend/server.py
# Server: http://localhost:8000
```

---

Roadmap

Phase Target Status
1 Core RAG pipeline In progress
2 Evaluation framework In progress
3 Data extraction pipeline In progress
4 Agentic automation In progress
5 Dashboard Planned
6 Production deployment Planned
7 GraphRAG integration Planned
8 Hybrid search and reranking Planned

---

Non-Goals

ATRRIC is not:

· A hosted product. You deploy and run it yourself, on your own infrastructure.
· An LLM provider. ATRRIC orchestrates models, local or API-based, but does not train or host its own.
· A general-purpose chatbot. It is purpose-built for structured market intelligence, not open-ended chat.
· A drop-in replacement for anything. It is a focused tool, not a platform.

---

Contributing

This project is in early development. Contributions, feedback, and bug reports are welcome. Please open an issue before submitting large changes.

---

License

MIT License. See LICENSE for details.
