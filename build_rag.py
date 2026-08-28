"""
build_rag.py - Atrric Industrial RAG Builder v2.0
==================================================
Fitur Power:
- Semantic Chunking (NLTK) + Parent-Child Chunking
- Rich Metadata dengan hash, timestamp, model info
- Progress Bar (tqdm) untuk monitoring
- Multiple File Support (semua .txt dalam data/)
- Logging System (terminal + file logs/build.log)
- Error Handling Robust (skip chunk rosak)
- Config-Driven (semua setting dari config.py)
- Hybrid Retrieval Preparation (metadata untuk BM25 nanti)
"""

import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import chromadb
import ollama
from tqdm import tqdm

# Import config
from config import DATA_DIR, CHROMA_DB_DIR

# ========== KONFIGURASI ==========
COLLECTION_NAME = "atrric_corpus"
EMBED_MODEL = "mxbai-embed-large"
CHUNK_SIZE = 500          # Saiz chunk (characters)
CHUNK_OVERLAP = 50        # Overlap antara chunk
PARENT_CHUNK_SIZE = 1000  # Untuk Parent-Child (konteks penuh)

# Setup logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "build.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== SEMANTIC CHUNKING ==========
def semantic_chunk(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Potong teks ikut ayat (semantic) dengan overlap.
    Fallback ke character-based kalau NLTK takde.
    """
    chunks = []
    
    # Cuba guna NLTK untuk sentence tokenization
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        from nltk.tokenize import sent_tokenize
        
        sentences = sent_tokenize(text)
        current_chunk = ""
        
        for sent in sentences:
            if len(current_chunk) + len(sent) <= chunk_size:
                current_chunk += sent + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + sent + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
    except Exception as e:
        logger.warning(f"⚠️ NLTK fallback ke character chunking: {e}")
        # Character-based chunking
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk.strip())
    
    return chunks

# ========== PARENT-CHILD CHUNKING ==========
def parent_child_chunk(text: str) -> Dict[str, List[str]]:
    """
    Hasilkan dua lapisan:
    - Child chunks (kecil, untuk retrieval tepat)
    - Parent chunks (besar, untuk konteks penuh)
    """
    # Child chunks: 500 chars
    child_chunks = semantic_chunk(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    
    # Parent chunks: 1000 chars (gabung child chunks)
    parent_chunks = []
    current_parent = ""
    for child in child_chunks:
        if len(current_parent) + len(child) <= PARENT_CHUNK_SIZE:
            current_parent += child + " "
        else:
            if current_parent:
                parent_chunks.append(current_parent.strip())
            current_parent = child + " "
    if current_parent:
        parent_chunks.append(current_parent.strip())
    
    return {
        "child_chunks": child_chunks,
        "parent_chunks": parent_chunks
    }

# ========== METADATA GENERATION ==========
def generate_metadata(
    file_path: Path,
    chunk_text: str,
    chunk_index: int,
    chunk_type: str = "child",
    parent_index: Optional[int] = None
) -> Dict[str, Any]:
    """
    Hasilkan metadata kaya untuk setiap chunk.
    """
    return {
        "source_file": file_path.name,
        "source_path": str(file_path),
        "chunk_index": chunk_index,
        "chunk_type": chunk_type,  # "child" atau "parent"
        "parent_index": parent_index if parent_index is not None else chunk_index,
        "chunk_hash": hashlib.md5(chunk_text.encode()).hexdigest()[:8],
        "chunk_length": len(chunk_text),
        "processed_at": datetime.now().isoformat(),
        "collection": COLLECTION_NAME,
        "embedding_model": EMBED_MODEL,
        "chunk_size": CHUNK_SIZE if chunk_type == "child" else PARENT_CHUNK_SIZE
    }

# ========== MAIN BUILD FUNCTION ==========
def build_index():
    """
    Proses utama: baca semua .txt, chunk, embed, simpan dalam ChromaDB.
    """
    logger.info("=" * 60)
    logger.info("🚀 ATRRIC INDUSTRIAL RAG BUILDER v2.0")
    logger.info("=" * 60)
    logger.info(f"📁 Data directory: {DATA_DIR}")
    logger.info(f"🗄️  Collection: {COLLECTION_NAME}")
    logger.info(f"🧠 Embedding model: {EMBED_MODEL}")
    logger.info(f"📏 Chunk size: {CHUNK_SIZE} chars (overlap: {CHUNK_OVERLAP})")
    logger.info(f"📏 Parent chunk size: {PARENT_CHUNK_SIZE} chars")
    logger.info("=" * 60)
    
    # 1. Get all text files
    txt_files = list(DATA_DIR.glob("*.txt"))
    if not txt_files:
        logger.error("❌ No .txt files found in data/ directory.")
        logger.info("💡 Please add at least one .txt file to data/")
        sys.exit(1)
    
    logger.info(f"📄 Found {len(txt_files)} text file(s):")
    for f in txt_files:
        logger.info(f"   - {f.name}")
    
    # 2. Connect to ChromaDB
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    
    # Reset collection for fresh build
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info("🔄 Removed existing collection")
    except:
        logger.info("🆕 Creating new collection")
    
    collection = client.create_collection(name=COLLECTION_NAME)
    
    # 3. Process each file with progress bar
    total_child_chunks = 0
    total_parent_chunks = 0
    total_files_processed = 0
    
    for file_path in tqdm(txt_files, desc="📖 Processing files", unit="file"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            logger.info(f"\n📖 Processing: {file_path.name} ({len(text)} chars)")
            
            # Generate Parent-Child chunks
            chunk_result = parent_child_chunk(text)
            child_chunks = chunk_result["child_chunks"]
            parent_chunks = chunk_result["parent_chunks"]
            
            logger.info(f"   ↳ Child chunks: {len(child_chunks)}")
            logger.info(f"   ↳ Parent chunks: {len(parent_chunks)}")
            
            # Store child chunks with their parent reference
            for idx, chunk in enumerate(child_chunks):
                if not chunk.strip():
                    continue
                    
                try:
                    embed = ollama.embeddings(model=EMBED_MODEL, prompt=chunk)["embedding"]
                    
                    # Parent index: cari parent yang mengandungi child ni
                    parent_idx = None
                    for p_idx, parent in enumerate(parent_chunks):
                        if chunk in parent:
                            parent_idx = p_idx
                            break
                    
                    meta = generate_metadata(
                        file_path, chunk, idx,
                        chunk_type="child",
                        parent_index=parent_idx
                    )
                    
                    collection.add(
                        ids=[f"{file_path.stem}_child_{idx}_{meta['chunk_hash']}"],
                        embeddings=[embed],
                        documents=[chunk],
                        metadatas=[meta]
                    )
                    total_child_chunks += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to embed child chunk {idx} in {file_path.name}: {e}")
                    continue
            
            # Store parent chunks
            for idx, chunk in enumerate(parent_chunks):
                if not chunk.strip():
                    continue
                    
                try:
                    embed = ollama.embeddings(model=EMBED_MODEL, prompt=chunk)["embedding"]
                    
                    meta = generate_metadata(
                        file_path, chunk, idx,
                        chunk_type="parent",
                        parent_index=idx
                    )
                    
                    collection.add(
                        ids=[f"{file_path.stem}_parent_{idx}_{meta['chunk_hash']}"],
                        embeddings=[embed],
                        documents=[chunk],
                        metadatas=[meta]
                    )
                    total_parent_chunks += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to embed parent chunk {idx} in {file_path.name}: {e}")
                    continue
            
            total_files_processed += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to process {file_path.name}: {e}")
            continue
    
    # 4. Final summary
    logger.info("=" * 60)
    logger.info("✅ BUILD COMPLETE")
    logger.info("=" * 60)
    logger.info(f"📄 Files processed: {total_files_processed}/{len(txt_files)}")
    logger.info(f"📦 Child chunks stored: {total_child_chunks}")
    logger.info(f"📦 Parent chunks stored: {total_parent_chunks}")
    logger.info(f"📦 Total chunks: {total_child_chunks + total_parent_chunks}")
    logger.info(f"🗄️  Collection: {COLLECTION_NAME}")
    logger.info(f"📁 ChromaDB path: {CHROMA_DB_DIR}")
    logger.info(f"📋 Log file: {LOG_DIR / 'build.log'}")
    logger.info("=" * 60)
    logger.info("🎉 Run: python query_rag.py 'your question'")

if __name__ == "__main__":
    build_index()