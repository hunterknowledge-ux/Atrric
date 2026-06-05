
# Atrric: Market Intelligence Engine (MVP)

A standalone, local-first market intelligence proof-of-concept (PoC) designed to analyze Malaysian Gen Z behavior and sentiment.

## 🚀 Overview
Atrric utilizes a local **Retrieval-Augmented Generation (RAG)** architecture to process unstructured data and allow semantic querying. The entire codebase was built by a non-traditional/outsider founder via highly efficient AI-assisted **vibe coding**, proving extreme execution capability with zero framework overhead.

## 🛠️ Technical Stack & Architecture
To maintain maximum control and privacy, the system is completely self-hosted and operates local-first:
- **Vector Database:** ChromaDB (Local deployment)
- **Embedding Model:** `mxbai-embed-large` (Open-source, running via Ollama)
- **Large Language Model (LLM):** `qwen2.5-coder:7b` (Open-source, running via Ollama)
- **Infrastructure:** GitHub Codespaces (2-core machine, 4GB RAM, 15GB storage)

## 📁 Core Functionality
- `build_rag.py`: Ingests raw `.txt` files, chunks text segments, generates vector embeddings, and stores them securely in the local ChromaDB.
- `query_rag.py`: Accepts user queries, performs vector semantic search to retrieve context, and feeds it into the local LLM for context-aware generation.

## 📈 Current Stage & Strategic Edge
- **Status:** Fully functional MVP tested with sample data pipelines.
- **Privacy by Design:** 100% local processing ensures absolute data sovereignty.
- **Zero Infra Cost:** Built entirely using free-tier services and open-source models, demonstrating capital efficiency.
- **Minimalist Codebase:** Under 200 lines of Python code for the core engine, allowing fast maintenance and iterations.

## 🎯 Next Steps
Transitioning into live-data ingestion testing and market validation to refine extraction accuracy and test core hypotheses.
