"""
test_build.py - Ujian untuk build_rag.py
==========================================
Fungsi: Pastikan build_rag.py berjalan tanpa error.
Cara guna: pytest tests/test_build.py
"""

import sys
import subprocess
from pathlib import Path

# Tambah root folder ke path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_build_runs():
    """Test: build_rag.py jalan tanpa error."""
    result = subprocess.run(
        ["python", "build_rag.py"],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    # Check output
    assert result.returncode == 0, f"Build failed: {result.stderr}"
    assert "BUILD COMPLETE" in result.stdout or "✅" in result.stdout, "Build not complete"

def test_chroma_db_created():
    """Test: ChromaDB folder wujud selepas build."""
    chroma_dir = Path("chroma_db")
    assert chroma_dir.exists(), "ChromaDB folder not created"
    
    # Check ada collection
    import chromadb
    client = chromadb.PersistentClient(path=str(chroma_dir))
    collections = client.list_collections()
    assert len(collections) > 0, "No collections found in ChromaDB"

def test_data_loaded():
    """Test: Data berjaya dimuatkan."""
    data_dir = Path("data")
    assert data_dir.exists(), "Data folder not found"
    
    txt_files = list(data_dir.glob("*.txt"))
    assert len(txt_files) > 0, "No .txt files found in data/"