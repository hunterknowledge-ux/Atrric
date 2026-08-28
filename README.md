
# Atrric: Agentic & Graph-Powered Market Intelligence Engine

A native-AI, local-first market intelligence platform engineered to map, correlate, and analyze Malaysian Gen Z behavior, sentiment, and trend propagation at scale.

## 🚀 Vision & Core Premise
Atrric operates as an enterprise-grade intelligence engine—combining Multi-Agent Orchestration, Knowledge Graphs, and Vector Retrieval to transform unstructured Big Data into actionable market insights. Built with data sovereignty in mind and zero framework bloat.

## 🛠️ Architecture
- **Agentic Orchestration:** Specialized AI Agents for autonomous ingestion, entity-relation extraction, self-correction, and complex analytical reasoning.
- **Hybrid GraphRAG Engine:** Blends Knowledge Graphs (for mapping multi-hop relationships between subcultures, slang, and spending behavior) with Vector DB semantic search.
- **Vector Database:** ChromaDB (Local deployment).
- **Local LLM Engine:** Ollama integration (`qwen2.5` / scalable to larger reasoning models).
- **Embedding Model:** `mxbai-embed-large`.
- **Infrastructure:** GitHub Codespaces (2-core machine, 4GB RAM).

## 📌 Core Capabilities
- **Autonomous Data Pipeline:** Agents process raw social media data, survey transcripts, and code-switching text (Manglish/Malay/English).
- **Multi-Hop Trend Analysis:** Uncovers non-obvious connections between cultural catalysts and financial habits.
- **Local-First Processing:** Fully self-hosted architecture ensuring absolute data privacy and zero API overhead.

## ⚡ Quickstart
```bash
# Clone repository
git clone [https://github.com/hunterknowledge-ux/Atrric.git](https://github.com/hunterknowledge-ux/Atrric.git)
cd Atrric

# Install dependencies
pip install -r requirements.txt

# Execute Pipeline
python build_rag.py
python query_rag.py