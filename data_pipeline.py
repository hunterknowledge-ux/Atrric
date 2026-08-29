"""
data_pipeline.py - ETL Pipeline untuk Big Data (Manglish Optimized)
================================================
Fungsi: Proses data mentah ke format siap untuk RAG.
        Khas untuk teks Manglish/Melayu/Inggeris.
Cara guna: python data_pipeline.py
"""

import os
import sys
import json
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# ======================================================================
# KONFIGURASI
# ======================================================================
RAW_DATA_DIR = Path(__file__).parent / "raw_data"
DATA_DIR = Path(__file__).parent / "data"
LOG_DIR = Path(__file__).parent / "logs"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Setup logging
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ======================================================================
# MANGLISH / MELAYU / INGGERIS PREPROCESSING
# ======================================================================

# Slang normalization dictionary
SLANG_MAP = {
    # Common Malay slang
    "x": "tak",
    "xtau": "tak tahu",
    "xde": "takde",
    "xpe": "takpe",
    "xnak": "tak nak",
    "xsuke": "tak suka",
    "k": "aku",
    "ko": "kau",
    "aku": "saya",
    "ko": "awak",
    "diorg": "mereka",
    "org": "orang",
    "sbb": "sebab",
    "sbbtu": "sebab tu",
    "sgt": "sangat",
    "sng": "senang",
    "skrg": "sekarang",
    "sbb": "sebab",
    "tp": "tapi",
    "tpi": "tapi",
    "tdk": "tak",
    "jgn": "jangan",
    "jd": "jadi",
    "jg": "juga",
    "pls": "tolong",
    "plz": "tolong",
    "bg": "bagi",
    "blh": "boleh",
    "byk": "banyak",
    "dpt": "dapat",
    "drp": "daripada",
    "dtg": "datang",
    "gne": "guna",
    "gni": "gini",
    "gt": "ada",
    "kek": "kekal",
    "kn": "kan",
    "la": "lah",
    "lg": "lagi",
    "mcm": "macam",
    "mkn": "makan",
    "mls": "malas",
    "mmg": "memang",
    "msk": "masuk",
    "nnt": "nanti",
    "pg": "pagi",
    "ptg": "petang",
    "rse": "rasa",
    "smp": "sampai",
    "smpi": "sampai",
    "tgh": "tengah",
    "tkt": "takut",
    "trs": "terus",
    "ttu": "terus",
    "wkt": "waktu",
    "y": "ya",
    "yg": "yang",
    
    # English slang common in Malaysia
    "u": "you",
    "ur": "your",
    "btw": "by the way",
    "idk": "saya tak tahu",
    "lol": "ketawa",
    "omg": "oh my god",
    "fr": "for real",
    "ngl": "not gonna lie",
    "imo": "in my opinion",
    "tbh": "to be honest",
    "rn": "right now",
    "afaik": "as far as i know",
    "ikr": "i know right",
    "fyi": "for your information",
}

def normalize_slang(text: str) -> str:
    """Normalize slang to standard Malay/English."""
    words = text.split()
    normalized = []
    for word in words:
        # Remove punctuation for lookup
        clean_word = re.sub(r'[^\w\s]', '', word.lower())
        if clean_word in SLANG_MAP:
            # Replace with normalized form, preserve original casing if possible
            norm = SLANG_MAP[clean_word]
            if word[0].isupper():
                norm = norm.capitalize()
            normalized.append(norm)
        else:
            normalized.append(word)
    return ' '.join(normalized)

def preprocess_manglish(text: str) -> str:
    """
    Preprocess teks Manglish/Melayu/Inggeris.
    1. Normalize slang
    2. Handle code-switching patterns
    3. Clean special characters
    """
    # Step 1: Normalize slang
    text = normalize_slang(text)
    
    # Step 2: Fix common code-switching patterns
    # Example: "aku suka makan nasi lemak" -> standard
    # Example: "i want to eat nasi lemak" -> keep as is
    
    # Step 3: Clean special characters
    # Remove excessive emojis (keep some for sentiment)
    # text = re.sub(r'[^\w\s.,!?@#%&*()\-:]', '', text)
    
    # Step 4: Normalize repeated characters (e.g., "sangatttt" -> "sangat")
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    
    # Step 5: Fix spacing
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def clean_text(text: str) -> str:
    """Bersihkan teks dengan preprocessing Manglish."""
    # Preprocess Manglish/Melayu/Inggeris
    text = preprocess_manglish(text)
    
    # Buang extra spaces
    text = ' '.join(text.split())
    
    # Buang repeated newlines
    while '\n\n\n' in text:
        text = text.replace('\n\n\n', '\n\n')
    
    return text.strip()

def semantic_chunk_manglish(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Potong teks dengan kesedaran bahasa tempatan.
    - Cuba split ikut ayat (., !, ?)
    - Kalau tak, split ikut paragraph
    - Kalau tak, split ikut karakter
    """
    chunks = []
    text = clean_text(text)
    
    # First: split by sentences (., !, ?)
    sentences = re.split(r'(?<=[.!?])\s+', text)
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
    
    # If chunks are too few or too large, fallback to paragraph split
    if len(chunks) <= 2:
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + para + "\n\n"
        if current_chunk:
            chunks.append(current_chunk.strip())
    
    return chunks

# ======================================================================
# FUNGSI UTAMA
# ======================================================================

def read_files() -> List[Dict]:
    """Baca semua fail dalam raw_data/"""
    files = []
    if not RAW_DATA_DIR.exists():
        logger.error(f"❌ Folder raw_data/ tidak dijumpai.")
        logger.info("💡 Buat folder raw_data/ dan letak fail mentah di dalamnya.")
        return files
    
    for file_path in RAW_DATA_DIR.glob("*"):
        if file_path.suffix in ['.txt', '.csv', '.md', '.json']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                files.append({
                    "name": file_path.name,
                    "content": content,
                    "size": len(content),
                    "type": file_path.suffix[1:] if file_path.suffix else 'txt'
                })
                logger.info(f"✅ Baca: {file_path.name} ({len(content)} aksara)")
            except Exception as e:
                logger.error(f"❌ Gagal baca {file_path.name}: {e}")
    
    return files

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Potong teks kepada chunks (guna semantic chunking untuk Manglish)."""
    return semantic_chunk_manglish(text, chunk_size, overlap)

def process_files(files: List[Dict]) -> Dict:
    """Process semua files dan hasilkan output"""
    results = {
        "total_files": len(files),
        "total_chunks": 0,
        "processed_files": [],
        "errors": []
    }
    
    for file_info in files:
        try:
            chunks = chunk_text(file_info["content"])
            
            # Save chunks to data folder
            output_file = DATA_DIR / f"processed_{file_info['name']}"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("\n\n".join(chunks))
            
            results["processed_files"].append({
                "name": file_info["name"],
                "original_size": file_info["size"],
                "chunks": len(chunks),
                "output": str(output_file)
            })
            results["total_chunks"] += len(chunks)
            
            logger.info(f"✅ Processed: {file_info['name']} -> {len(chunks)} chunks")
            
        except Exception as e:
            results["errors"].append(f"{file_info['name']}: {e}")
            logger.error(f"❌ Failed: {file_info['name']} - {e}")
    
    return results

def save_report(results: Dict):
    """Simpan report proses"""
    report_file = DATA_DIR / "pipeline_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2, ensure_ascii=False)
    logger.info(f"📄 Report saved: {report_file}")

# ======================================================================
# MAIN
# ======================================================================
def main():
    logger.info("=" * 60)
    logger.info("📦 DATA PIPELINE - ETL untuk Big Data (Manglish Optimized)")
    logger.info("=" * 60)
    
    # Check raw_data folder
    if not RAW_DATA_DIR.exists():
        RAW_DATA_DIR.mkdir()
        logger.info(f"✅ Created {RAW_DATA_DIR}/")
        logger.info("💡 Letak fail mentah (.txt, .csv, .md) dalam folder ini.")
        return
    
    # Read files
    files = read_files()
    if not files:
        logger.warning("⚠️ Tiada fail dalam raw_data/")
        return
    
    # Process
    logger.info(f"📄 Processing {len(files)} files...")
    results = process_files(files)
    
    # Save report
    save_report(results)
    
    # Summary
    logger.info("=" * 60)
    logger.info("✅ PIPELINE COMPLETE")
    logger.info(f"📄 Files: {results['total_files']}")
    logger.info(f"📦 Chunks: {results['total_chunks']}")
    if results['errors']:
        logger.warning(f"⚠️ Errors: {len(results['errors'])}")
    logger.info(f"📁 Data ready in {DATA_DIR}/")
    logger.info("💡 Run: python build_rag.py")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()