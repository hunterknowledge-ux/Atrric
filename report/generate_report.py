import sqlite3
import json
import urllib.request
import os
from dotenv import load_dotenv
from core.rag import _get_rag

load_dotenv()
ILMU_API_KEY = os.getenv("ILMU_API_KEY")
ILMU_URL = "https://api.ilmu.ai/v1/chat/completions"

def get_spatial_data():
    try:
        conn = sqlite3.connect('raw_data/spatial/atrric_macro.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT district, SUM(CAST(population AS REAL)) as total
            FROM population_data
            WHERE state = 'Selangor' AND (age = '15-19' OR age = '20-24') AND sex = 'both' AND ethnicity = 'overall'
            GROUP BY district ORDER BY total DESC LIMIT 3
        """)
        data = cursor.fetchall()
        conn.close()
        return "\n".join([f"- {r[0]}: {r[1]} ribu Gen Z" for r in data])
    except Exception as e:
        return "- Data spatial tidak dijumpai."

def get_news_data():
    try:
        conn = sqlite3.connect('raw_data/news/atrric_news.db')
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM news ORDER BY id DESC LIMIT 3")
        data = cursor.fetchall()
        conn.close()
        return "\n".join([f"- {r[0]}" for r in data])
    except Exception as e:
        return "- Data berita tidak dijumpai."

def get_genz_quotes():
    try:
        rag = _get_rag()
        results = rag.retrieve("pandangan gen z pasal kos hidup, gaji, dan peluang kerja", limit=3)
        return "\n".join([f"- \"{getattr(r, 'text', str(r))[:200]}...\"" for r in results])
    except Exception as e:
        return "- Data RAG tidak dijumpai."

def generate_report():
    print("⏳ Mengumpul data Spatial, Berita, dan Komen (RAG)...")
    spatial = get_spatial_data()
    news = get_news_data()
    quotes = get_genz_quotes()

    system_prompt = """Kau adalah Penganalisis Risiko Geopolitik & Sosio-Ekonomi. 
Buat analisis kausal (Causal Analysis) antara Trigger (Berita), Spatial (Kepadatan), dan Ground Truth (Komen). 
JANGAN ringkaskan berita. Terus bagi Insight tajam dalam 3 perenggan. Tiada mukadimah."""

    user_prompt = f"""
DATA SPATIAL (Kepadatan Gen Z di Selangor):
{spatial}

DATA TRIGGER (Berita Terkini):
{news}

DATA GROUND TRUTH (Komen Gen Z):
{quotes}

Tugasan: Hasilkan laporan analisis kausal dalam 3 perenggan.
P1: Trigger (Pilih 1 berita paling kritikal).
P2: Spatial Impact (Kaitkan dengan kepadatan Gen Z).
P3: Reality Check (Guna data Komen untuk tunjuk reaksi sebenar).
"""

    headers = {"Authorization": f"Bearer {ILMU_API_KEY}", "Content-Type": "application/json"}
    body = {
"model": "ilmu-mini-v3.3",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 800,
        "temperature": 0.4
    }

    print("🧠 Menghantar data ke ILMU API untuk sintesis...")
    try:
        req = urllib.request.Request(ILMU_URL, data=json.dumps(body).encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            analysis = res_data['choices'][0]['message']['content']
            
            print("\n" + "="*60)
            print("📊 ATRRIC SYSTEMIC REPORT (EXPERT MODE)")
            print("="*60 + "\n")
            print(analysis)
            print("\n" + "="*60)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    generate_report()
