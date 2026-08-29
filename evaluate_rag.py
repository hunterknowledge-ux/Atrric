"""
evaluate_rag.py - Atrric Performance Evaluation Tool
====================================================
Fungsi: Ukur prestasi RAG dengan set soalan ujian.
Metrik: Hit Rate (HR) dan Mean Reciprocal Rank (MRR).
Output: Report dalam JSON dan Markdown.

Cara guna:
1. Sediakan test_set.json dalam folder data/
2. python evaluate_rag.py
"""

import json
import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime

# ======================================================================
# KONFIGURASI
# ======================================================================
TEST_SET_FILE = Path(__file__).parent / "data" / "test_set.json"
OUTPUT_DIR = Path(__file__).parent / "evaluation"
OUTPUT_DIR.mkdir(exist_ok=True)

# ======================================================================
# BACA TEST SET
# ======================================================================
def load_test_set():
    """Load test set dari file JSON."""
    if not TEST_SET_FILE.exists():
        print(f"❌ Test set not found: {TEST_SET_FILE}")
        print("💡 Please create data/test_set.json with your test questions.")
        print("   Format: [{\"question\": \"...\", \"expected\": \"...\"}]")
        sys.exit(1)
    
    with open(TEST_SET_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ======================================================================
# JALANKAN QUERY
# ======================================================================
def run_query(question: str) -> dict:
    """Jalankan query_rag.py dan dapatkan hasil."""
    try:
        result = subprocess.run(
            ["python", "query_rag.py", question],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        output = result.stdout + result.stderr
        
        # Extract response
        response_match = re.search(r"📌 Jawapan:\n(.*?)\n\n", output, re.DOTALL)
        response = response_match.group(1).strip() if response_match else ""
        
        # Extract confidence
        confidence_match = re.search(r"Keyakinan keseluruhan: ([\d.]+)%", output)
        confidence = float(confidence_match.group(1)) / 100 if confidence_match else 0.0
        
        # Extract sources
        sources = []
        for line in output.split("\n"):
            if "confidence:" in line and "source" in line:
                sources.append(line.strip())
        
        return {
            "response": response,
            "confidence": confidence,
            "sources": sources,
            "success": len(response) > 0
        }
    except subprocess.TimeoutExpired:
        return {"response": "", "confidence": 0, "sources": [], "success": False, "error": "Timeout"}
    except Exception as e:
        return {"response": "", "confidence": 0, "sources": [], "success": False, "error": str(e)}

# ======================================================================
# EVALUATE
# ======================================================================
def evaluate_hr_mrr(test_set: list, results: list) -> dict:
    """Calculate Hit Rate and MRR."""
    hits = 0
    reciprocal_ranks = []
    
    for i, result in enumerate(results):
        if not result["success"]:
            continue
        
        # Check if expected answer appears in response (simple contains check)
        expected = test_set[i]["expected"].lower()
        response = result["response"].lower()
        
        if expected in response or response in expected:
            hits += 1
            reciprocal_ranks.append(1.0)  # Rank 1
        else:
            reciprocal_ranks.append(0.0)
    
    hit_rate = hits / len(test_set) if test_set else 0
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0
    
    return {
        "hit_rate": hit_rate,
        "mrr": mrr,
        "total_questions": len(test_set),
        "hits": hits,
        "ranked": reciprocal_ranks
    }

# ======================================================================
# GENERATE REPORT
# ======================================================================
def generate_report(test_set: list, results: list, metrics: dict):
    """Hasilkan report dalam JSON dan Markdown."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # ========== JSON REPORT ==========
    json_report = {
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "details": [
            {
                "question": test_set[i]["question"],
                "expected": test_set[i]["expected"],
                "response": results[i]["response"],
                "confidence": results[i]["confidence"],
                "success": results[i]["success"],
                "sources": results[i]["sources"]
            }
            for i in range(len(test_set))
        ]
    }
    
    json_file = OUTPUT_DIR / f"report_{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_report, f, indent=2, ensure_ascii=False)
    
    # ========== MARKDOWN REPORT ==========
    md_file = OUTPUT_DIR / f"report_{timestamp}.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(f"# Atrric Evaluation Report\n\n")
        f.write(f"**Tarikh:** {datetime.now().strftime('%d %B %Y, %H:%M')}\n\n")
        
        f.write("## Metrics\n\n")
        f.write(f"- **Hit Rate:** {metrics['hit_rate']:.2%}\n")
        f.write(f"- **MRR:** {metrics['mrr']:.4f}\n")
        f.write(f"- **Total Questions:** {metrics['total_questions']}\n")
        f.write(f"- **Hits:** {metrics['hits']}\n\n")
        
        f.write("## Details\n\n")
        for i, item in enumerate(json_report["details"]):
            f.write(f"### Question {i+1}: {item['question']}\n\n")
            f.write(f"**Expected:** {item['expected']}\n\n")
            f.write(f"**Response:** {item['response']}\n\n")
            f.write(f"**Confidence:** {item['confidence']:.2%}\n\n")
            f.write(f"**Sources:** {len(item['sources'])}\n\n")
            f.write("---\n\n")
    
    return json_file, md_file

# ======================================================================
# MAIN
# ======================================================================
def main():
    print("=" * 60)
    print("🧪 ATRRIC EVALUATION TOOL")
    print("=" * 60)
    
    # Load test set
    test_set = load_test_set()
    print(f"📄 Loaded {len(test_set)} test questions")
    
    # Run queries
    print("\n🔄 Running queries...")
    results = []
    for i, item in enumerate(test_set):
        print(f"   [{i+1}/{len(test_set)}] {item['question'][:50]}...")
        result = run_query(item["question"])
        results.append(result)
    
    # Evaluate
    metrics = evaluate_hr_mrr(test_set, results)
    
    # Generate report
    json_file, md_file = generate_report(test_set, results, metrics)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ EVALUATION COMPLETE")
    print("=" * 60)
    print(f"📊 Hit Rate: {metrics['hit_rate']:.2%}")
    print(f"📊 MRR: {metrics['mrr']:.4f}")
    print(f"📄 Report (JSON): {json_file}")
    print(f"📄 Report (Markdown): {md_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()