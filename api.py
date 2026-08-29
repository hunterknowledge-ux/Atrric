"""
api.py - Atrric Web API
=====================================================================
Fungsi: Jadikan Atrric sebagai web service.
Endpoints:
- GET /query?q=soalan&top_k=3&temperature=0.7
- GET /health
- GET /stats
- POST /query (JSON body)

Cara guna:
1. pip install fastapi uvicorn
2. python api.py
3. Buka browser: http://localhost:8000/query?q=apa+itu+gen+z
=====================================================================
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import chromadb
import ollama

# ======================================================================
# KONFIGURASI
# ======================================================================
from config import CHROMA_DB_DIR

COLLECTION_NAME = "atrric_corpus"
EMBED_MODEL = "mxbai-embed-large"
LLM_MODEL = "qwen2.5:1.5b"

# ======================================================================
# SYSTEM PROMPT (Ringkas untuk API)
# ======================================================================
SYSTEM_PROMPT = """Anda adalah Atrric, sistem Kecerdasan Pasaran untuk Gen Z Malaysia.
Jawab soalan berdasarkan data yang diberikan.
Jika data tidak mencukupi, katakan 'Data sedia ada tidak mencukupi'.
Jawab dalam Bahasa Melayu atau Inggeris ikut soalan.
Berikan jawapan ringkas dan berfokus kepada fakta.
Jika perlu, berikan cadangan tindakan untuk perniagaan.
Sasaran audiens: Pengarah, pengurus, pelabur."""

# ======================================================================
# FASTAPI APP
# ======================================================================
app = FastAPI(
    title="Atrric API",
    description="Market Intelligence untuk Gen Z Malaysia",
    version="1.0.0"
)

# ======================================================================
# MODELS
# ======================================================================
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3
    temperature: Optional[float] = 0.7

class QueryResponse(BaseModel):
    query: str
    response: str
    sources: list
    confidence: float
    elapsed_time: float
    timestamp: str

# ======================================================================
# GLOBAL CLIENT
# ======================================================================
client = None
collection = None
telemetry = {"total_queries": 0, "queries": []}

def init_chromadb():
    """Initialise ChromaDB connection."""
    global client, collection
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        collection = client.get_collection(name=COLLECTION_NAME)
        return True
    except Exception as e:
        print(f"❌ ChromaDB Error: {e}")
        return False

# ======================================================================
# CORE FUNCTION
# ======================================================================
def run_query(query: str, top_k: int = 3, temperature: float = 0.7) -> dict:
    """Execute query and return response."""
    start_time = time.time()
    
    # Generate embedding
    try:
        embed = ollama.embeddings(model=EMBED_MODEL, prompt=query)["embedding"]
    except Exception as e:
        return {"error": f"Ollama embedding error: {e}", "response": "", "sources": [], "confidence": 0.0}
    
    # Query ChromaDB
    results = collection.query(
        query_embeddings=[embed],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    
    # Fallback
    if not results.get("documents") or not results["documents"][0]:
        try:
            response = ollama.chat(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": query}],
                options={"temperature": temperature}
            )
            return {
                "response": response['message']['content'],
                "sources": [],
                "confidence": 0.0,
                "elapsed_time": time.time() - start_time
            }
        except Exception as e:
            return {"error": f"Ollama fallback error: {e}", "response": "", "sources": [], "confidence": 0.0}
    
    # Generate response
    context = "\n\n".join(results['documents'][0])
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Data:\n{context}\n\nSoalan: {query}"}
    ]
    
    try:
        response = ollama.chat(
            model=LLM_MODEL,
            messages=messages,
            options={"temperature": temperature, "max_tokens": 500}
        )
    except Exception as e:
        return {"error": f"Ollama generation error: {e}", "response": "", "sources": [], "confidence": 0.0}
    
    # Calculate confidence
    avg_confidence = 1 - (sum(results['distances'][0]) / len(results['distances'][0])) if results.get('distances') else 0
    
    # Build sources
    sources = []
    for i, meta in enumerate(results['metadatas'][0]):
        confidence = 1 - results['distances'][0][i]
        sources.append({
            "source": meta.get('source_file', 'unknown'),
            "confidence": confidence,
            "type": meta.get('chunk_type', 'child')
        })
    
    # Update telemetry
    telemetry["total_queries"] += 1
    telemetry["queries"].append({
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "source_count": len(sources)
    })
    if len(telemetry["queries"]) > 100:
        telemetry["queries"] = telemetry["queries"][-100:]
    
    return {
        "response": response['message']['content'],
        "sources": sources,
        "confidence": avg_confidence,
        "elapsed_time": time.time() - start_time
    }

# ======================================================================
# ENDPOINTS
# ======================================================================

@app.get("/")
async def root():
    return {
        "name": "Atrric API",
        "version": "1.0.0",
        "endpoints": [
            "/query?q=...&top_k=3&temperature=0.7",
            "/health",
            "/stats"
        ],
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    """Check status sistem."""
    status = {
        "status": "healthy",
        "chromadb": False,
        "ollama": False,
        "timestamp": datetime.now().isoformat()
    }
    
    # Check ChromaDB
    try:
        if collection:
            collection.count()
            status["chromadb"] = True
    except:
        pass
    
    # Check Ollama
    try:
        ollama.list()
        status["ollama"] = True
    except:
        pass
    
    if not status["chromadb"] or not status["ollama"]:
        status["status"] = "degraded"
    
    return status

@app.get("/stats")
async def stats():
    """Tunjukkan telemetry."""
    return {
        "total_queries": telemetry["total_queries"],
        "recent_queries": telemetry["queries"][-10:],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/query")
async def query_get(
    q: str = Query(..., description="Soalan anda"),
    top_k: int = Query(3, ge=1, le=10, description="Bilangan dokumen"),
    temperature: float = Query(0.7, ge=0.0, le=2.0, description="Kreativiti")
):
    """Query endpoint (GET)."""
    if not collection:
        if not init_chromadb():
            raise HTTPException(status_code=503, detail="ChromaDB not available")
    
    if not q or len(q.strip()) < 3:
        raise HTTPException(status_code=400, detail="Soalan terlalu pendek")
    
    result = run_query(q, top_k, temperature)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return {
        "query": q,
        "response": result["response"],
        "sources": result["sources"],
        "confidence": result["confidence"],
        "elapsed_time": result["elapsed_time"],
        "timestamp": datetime.now().isoformat()
    }

@app.post("/query")
async def query_post(request: QueryRequest):
    """Query endpoint (POST)."""
    if not collection:
        if not init_chromadb():
            raise HTTPException(status_code=503, detail="ChromaDB not available")
    
    if not request.query or len(request.query.strip()) < 3:
        raise HTTPException(status_code=400, detail="Soalan terlalu pendek")
    
    result = run_query(request.query, request.top_k, request.temperature)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return {
        "query": request.query,
        "response": result["response"],
        "sources": result["sources"],
        "confidence": result["confidence"],
        "elapsed_time": result["elapsed_time"],
        "timestamp": datetime.now().isoformat()
    }

# ======================================================================
# MAIN
# ======================================================================
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 ATRRIC WEB API")
    print("=" * 60)
    
    # Init ChromaDB
    if init_chromadb():
        print("✅ ChromaDB connected")
    else:
        print("❌ ChromaDB connection failed")
    
    print("🌐 Server starting at http://localhost:8000")
    print("📚 API docs: http://localhost:8000/docs")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)