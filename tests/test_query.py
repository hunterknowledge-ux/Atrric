"""
test_query.py - Ujian untuk query_rag.py
==========================================
Fungsi: Pastikan query_rag.py berfungsi.
Cara guna: pytest tests/test_query.py
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_query_returns_response():
    """Test: query_rag.py bagi jawapan."""
    result = subprocess.run(
        ["python", "query_rag.py", "apa itu gen z"],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    # Check output
    assert result.returncode == 0, f"Query failed: {result.stderr}"
    assert "📌 Jawapan:" in result.stdout, "No response found"
    assert len(result.stdout) > 100, "Response too short"

def test_query_with_json():
    """Test: query_rag.py --json output valid JSON."""
    result = subprocess.run(
        ["python", "query_rag.py", "apa itu gen z", "--json"],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    assert result.returncode == 0, f"JSON query failed: {result.stderr}"
    assert "{" in result.stdout, "No JSON output found"

def test_query_fallback():
    """Test: query_rag.py handle soalan kosong."""
    result = subprocess.run(
        ["python", "query_rag.py", ""],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    # Should exit with error or warning
    assert result.returncode != 0 or "⚠️" in result.stdout, "Empty query not handled"