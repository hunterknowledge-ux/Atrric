"""
data_pipeline.py - ETL Pipeline untuk Big Data
================================================
Fungsi: Proses data mentah ke format siap untuk RAG.
Cara guna: python data_pipeline.py
"""

import os
import sys
import json
import logging
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
        if file_path.suffix in ['.txt', '.csv', '.md']:
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

def clean_text(text: str) -> str:
    """Bersihkan teks"""
    # Buang extra spaces
    text = ' '.join(text.split())
    # Buang repeated newlines
    while '\n\n\n' in text:
        text = text.replace('\n\n\n', '\n\n')
    return text.strip()

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Potong teks kepada chunks"""
    chunks = []
    text = clean_text(text)
    
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # Start new chunk with overlap
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_text + para + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

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
    logger.info("📦 DATA PIPELINE - ETL untuk Big Data")
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