"""
evaluate_rag.py - Atrric Performance Evaluation Tool
====================================================
Fungsi: Ukur prestasi RAG dengan set soalan ujian.
Metrik: Hit Rate (HR), Mean Reciprocal Rank (MRR),
        Faithfulness, dan Answer Relevancy.
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
            "success": len(response) > 0,
            "full_output": output  # Simpan full output untuk context extraction
        }
    except subprocess.TimeoutExpired:
        return {"response": "", "confidence": 0, "sources": [], "success": False, "error": "Timeout"}
    except Exception as e:
        return {"response": "", "confidence": 0, "sources": [], "success": False, "error": str(e)}

# ======================================================================
# EVALUATE HIT RATE & MRR
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
            reciprocal_ranks.append(1.0)
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
# FAITHFULNESS & RELEVANCY (GUNA LLM)
# ======================================================================
def evaluate_faithfulness(context: str, response: str) -> float:
    """
    Guna LLM untuk nilai faithfulness (jawapan based on context).
    Skor 0.0 - 1.0.
    """
    if not context or not response:
        return 0.0
    
    prompt = f"""Anda adalah penilai RAG. Tugas: nilai sama ada jawapan ini adalah SETIA (faithful) kepada konteks yang diberikan.

Konteks: {context[:1500]}

Jawapan: {response}

Berikan skor 0.0 hingga 1.0:
- 1.0 = Jawapan SEPENUHNYA berdasarkan konteks
- 0.5 = Jawapan SEPARUH berdasarkan konteks, ada andaian tambahan
- 0.0 = Jawapan TIDAK berdasarkan konteks sama sekali

Output: Hanya nombor skor (contoh: 0.85). Jangan tulis apa-apa lain."""

    try:
        import ollama
        result = ollama.chat(
            model="qwen2.5:1.5b",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.0, "max_tokens": 10}
        )
        score = float(result['message']['content'].strip())
        return max(0.0, min(1.0, score))
    except:
        return 0.5  # default jika error

def evaluate_relevancy(query: str, response: str) -> float:
    """
    Guna LLM untuk nilai relevancy (jawapan jawab soalan ke tak).
    Skor 0.0 - 1.0.
    """
    if not query or not response:
        return 0.0
    
    prompt = f"""Anda adalah penilai RAG. Tugas: nilai sama ada jawapan ini RELEVAN dengan soalan.

Soalan: {query}
Jawapan: {response}

Berikan skor 0.0 hingga 1.0:
- 1.0 = Jawapan TERUS menjawab soalan
- 0.5 = Jawapan SEPARUH menjawab soalan
- 0.0 = Jawapan TIDAK relevan langsung

Output: Hanya nombor skor (contoh: 0.9). Jangan tulis apa-apa lain."""

    try:
        import ollama
        result = ollama.chat(
            model="qwen2.5:1.5b",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.0, "max_tokens": 10}
        )
        score = float(result['message']['content'].strip())
        return max(0.0, min(1.0, score))
    except:
        return 0.5  # default jika error

def extract_context_from_output(full_output: str) -> str:
    """Extract context dari output query_rag.py."""
    # Cuba cari "Data:" atau "Konteks:" dalam output
    context_match = re.search(r"Data:\n(.*?)\n\n", full_output, re.DOTALL)
    if context_match:
        return context_match.group(1).strip()
    
    # Fallback: cari apa-apa antara "📌 Jawapan:" dan "🔎"
    context_match = re.search(r"📌 Jawapan:\n(.*?)\n\n", full_output, re.DOTALL)
    if context_match:
        return context_match.group(1).strip()
    
    return ""

# ======================================================================
# GENERATE REPORT
# ======================================================================
def generate_report(test_set: list, results: list, metrics: dict, faith_scores: list, rel_scores: list):
    """Hasilkan report dalam JSON dan Markdown."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    avg_faithfulness = sum(faith_scores) / len(faith_scores) if faith_scores else 0
    avg_relevancy = sum(rel_scores) / len(rel_scores) if rel_scores else 0
    
    # ========== JSON REPORT ==========
    json_report = {
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            **metrics,
            "avg_faithfulness": avg_faithfulness,
            "avg_relevancy": avg_relevancy
        },
        "details": [
            {
                "question": test_set[i]["question"],
                "expected": test_set[i]["expected"],
                "response": results[i]["response"],
                "confidence": results[i]["confidence"],
                "faithfulness": faith_scores[i] if i < len(faith_scores) else 0,
                "relevancy": rel_scores[i] if i < len(rel_scores) else 0,
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
        f.write(f"- **Faithfulness:** {avg_faithfulness:.2%}\n")
        f.write(f"- **Answer Relevancy:** {avg_relevancy:.2%}\n")
        f.write(f"- **Total Questions:** {metrics['total_questions']}\n")
        f.write(f"- **Hits:** {metrics['hits']}\n\n")
        
        f.write("## Details\n\n")
        for i, item in enumerate(json_report["details"]):
            f.write(f"### Question {i+1}: {item['question']}\n\n")
            f.write(f"**Expected:** {item['expected']}\n\n")
            f.write(f"**Response:** {item['response']}\n\n")
            f.write(f"**Confidence:** {item['confidence']:.2%}\n\n")
            f.write(f"**Faithfulness:** {item['faithfulness']:.2%}\n\n")
            f.write(f"**Relevancy:** {item['relevancy']:.2%}\n\n")
            f.write(f"**Sources:** {len(item['sources'])}\n\n")
            f.write("---\n\n")
    
    return json_file, md_file

# ======================================================================
# MAIN
# ======================================================================
def main():
    print("=" * 60)
    print("🧪 ATRRIC EVALUATION TOOL v2.0")
    print("📊 Metrik: Hit Rate, MRR, Faithfulness, Relevancy")
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
    
    # Evaluate Hit Rate & MRR
    metrics = evaluate_hr_mrr(test_set, results)
    
    # Evaluate Faithfulness & Relevancy (guna LLM)
    print("\n🧠 Evaluating Faithfulness & Relevancy...")
    faith_scores = []
    rel_scores = []
    
    for i, result in enumerate(results):
        if result["success"]:
            context = extract_context_from_output(result.get("full_output", ""))
            faith = evaluate_faithfulness(context, result["response"])
            rel = evaluate_relevancy(test_set[i]["question"], result["response"])
            faith_scores.append(faith)
            rel_scores.append(rel)
            print(f"   [{i+1}] Faithfulness: {faith:.2f} | Relevancy: {rel:.2f}")
        else:
            faith_scores.append(0.0)
            rel_scores.append(0.0)
    
    # Generate report
    json_file, md_file = generate_report(test_set, results, metrics, faith_scores, rel_scores)
    
    # Summary
    avg_faith = sum(faith_scores) / len(faith_scores) if faith_scores else 0
    avg_rel = sum(rel_scores) / len(rel_scores) if rel_scores else 0
    
    print("\n" + "=" * 60)
    print("✅ EVALUATION COMPLETE")
    print("=" * 60)
    print(f"📊 Hit Rate: {metrics['hit_rate']:.2%}")
    print(f"📊 MRR: {metrics['mrr']:.4f}")
    print(f"📊 Faithfulness: {avg_faith:.2%}")
    print(f"📊 Answer Relevancy: {avg_rel:.2%}")
    print(f"📄 Report (JSON): {json_file}")
    print(f"📄 Report (Markdown): {md_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()