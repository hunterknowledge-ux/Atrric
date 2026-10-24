import json
import os
import sqlite3
import urllib.request

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string

load_dotenv()
app = Flask(__name__)

ILMU_API_KEY = os.getenv("ILMU_API_KEY")
ILMU_URL = "https://api.ilmu.ai/v1/chat/completions"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Atrric Command Center</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; }
        .card { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
        .glow { box-shadow: 0 0 15px rgba(59, 130, 246, 0.3); }
        .fade-in { animation: fadeIn 1s ease-in-out; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
    </style>
</head>
<body class="p-4 pb-12">
    <div class="max-w-5xl mx-auto">
        <!-- HEADER -->
        <header class="flex justify-between items-center mb-6 border-b border-slate-700 pb-4">
            <div>
                <h1 class="text-3xl font-bold text-blue-400 tracking-tight">ATRRIC</h1>
                <p class="text-slate-400 text-xs font-mono">SYSTEMIC INTELLIGENCE // V3.0</p>
            </div>
            <span class="bg-blue-900/50 text-blue-300 border border-blue-700 text-xs px-3 py-1 rounded-full animate-pulse">
                ● LIVE DATA
            </span>
        </header>

        <!-- ROW 1: CHARTS -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <!-- Bar Chart: Spatial -->
            <div class="card p-4 md:col-span-2 fade-in">
                <h2 class="text-sm font-semibold text-emerald-400 mb-3 flex items-center gap-2">
                    📍 GEN Z DENSITY (SELANGOR)
                </h2>
                <div class="h-48 w-full"><canvas id="spatialChart"></canvas></div>
            </div>
            <!-- Doughnut Chart: News Levels -->
            <div class="card p-4 fade-in" style="animation-delay: 0.2s;">
                <h2 class="text-sm font-semibold text-purple-400 mb-3 flex items-center gap-2">
                    🌐 NEWS LEVEL (GLOBAL VS NATIONAL)
                </h2>
                <div class="h-48 w-full flex justify-center"><canvas id="levelChart"></canvas></div>
            </div>
        </div>

        <!-- ROW 2: TIMELINE -->
        <div class="card p-4 mb-6 fade-in" style="animation-delay: 0.4s;">
            <h2 class="text-sm font-semibold text-yellow-400 mb-3 flex items-center gap-2">
                📈 NEWS TIMELINE (LAST 7 DAYS)
            </h2>
            <div class="h-32 w-full"><canvas id="timelineChart"></canvas></div>
        </div>

        <!-- ROW 3: SYNTHESIS ENGINE -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Live News Feed -->
            <div class="card p-4 fade-in" style="animation-delay: 0.6s;">
                <h2 class="text-sm font-semibold text-blue-400 mb-3 flex items-center gap-2">
                    📰 LIVE TRIGGERS FEED
                </h2>
                <div id="newsFeed" class="space-y-3 max-h-96 overflow-y-auto pr-2">
                    <!-- News loaded via JS -->
                </div>
            </div>

            <!-- AI Analysis -->
            <div class="card p-4 fade-in glow" style="animation-delay: 0.8s;">
                <h2 class="text-sm font-semibold text-pink-400 mb-3 flex items-center gap-2">
                    🧠 SYNTHESIS ENGINE
                </h2>
                <p class="text-slate-400 text-xs mb-3">Sintesis data Spatial + News + Gen Z Ground Truth.</p>
                
                <button onclick="runSynthesis()" id="synthBtn" class="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-bold py-2 px-4 rounded w-full transition transform hover:scale-[1.02]">
                    RUN SYSTEMIC ANALYSIS
                </button>

                <div id="analysisResult" class="mt-4 hidden bg-slate-900 p-4 rounded border border-slate-700 text-xs leading-relaxed text-slate-300 max-h-96 overflow-y-auto">
                </div>
            </div>
        </div>
    </div>

    <script>
        // 1. SPATIAL BAR CHART
        fetch('/api/spatial').then(res => res.json()).then(data => {
            new Chart(document.getElementById('spatialChart'), {
                type: 'bar',
                data: { labels: data.labels, datasets: [{ label: 'Gen Z (k)', data: data.values, backgroundColor: 'rgba(16, 185, 129, 0.7)', borderColor: '#10b981', borderWidth: 1, borderRadius: 4 }] },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { ticks: { color: '#94a3b8', font: {size: 10} }, grid: { color: '#334155' } }, x: { ticks: { color: '#94a3b8', font: {size: 10} }, grid: { display: false } } } }
            });
        });

        // 2. LEVEL DOUGHNUT CHART
        fetch('/api/news_level').then(res => res.json()).then(data => {
            new Chart(document.getElementById('levelChart'), {
                type: 'doughnut',
                data: { labels: data.labels, datasets: [{ data: data.values, backgroundColor: ['#8b5cf6', '#3b82f6'], borderWidth: 0 }] },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: {size: 10}, boxWidth: 12 } } }, cutout: '70%' }
            });
        });

        // 3. TIMELINE CHART
        fetch('/api/news_timeline').then(res => res.json()).then(data => {
            new Chart(document.getElementById('timelineChart'), {
                type: 'line',
                data: { labels: data.labels, datasets: [{ label: 'Berita', data: data.values, borderColor: '#eab308', backgroundColor: 'rgba(234, 179, 8, 0.1)', fill: true, tension: 0.4, pointRadius: 3 }] },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { color: '#94a3b8', font: {size: 10} }, grid: { color: '#334155' } }, x: { ticks: { color: '#94a3b8', font: {size: 10} }, grid: { display: false } } } }
            });
        });

        // 4. LIVE NEWS FEED
        fetch('/api/news').then(res => res.json()).then(data => {
            const feed = document.getElementById('newsFeed');
            data.forEach(item => {
                const el = document.createElement('div');
                el.className = 'border-l-2 border-blue-500 pl-3 py-1 hover:bg-slate-800 transition cursor-pointer';
                el.innerHTML = `
                    <div class="flex justify-between items-start">
                        <span class="text-[10px] text-slate-500 font-mono">${item.date} | ${item.level}</span>
                        <span class="text-[9px] bg-slate-700 px-1.5 py-0.5 rounded text-blue-300 truncate max-w-[80px]">${item.tags.split(',')[0]}</span>
                    </div>
                    <h3 class="text-xs font-semibold text-slate-200 mt-1 leading-snug">${item.title}</h3>
                    <p class="text-[10px] text-slate-400 mt-1 line-clamp-2">${item.content}</p>
                `;
                feed.appendChild(el);
            });
        });

        // 5. SYNTHESIS
        async function runSynthesis() {
            const btn = document.getElementById('synthBtn');
            const resultDiv = document.getElementById('analysisResult');
            btn.innerText = "ANALYZING..."; btn.disabled = true; btn.classList.add('opacity-50');
            resultDiv.classList.remove('hidden');
            resultDiv.innerHTML = '<span class="animate-pulse text-pink-400">Memproses sintesis data...</span>';
            try {
                const response = await fetch('/api/synthesize', { method: 'POST' });
                const data = await response.json();
                if(data.error) resultDiv.innerHTML = `<span class="text-red-400">Error: ${data.error}</span>`;
                else resultDiv.innerHTML = data.analysis.replace(/\\n/g, '<br>');
            } catch (e) { resultDiv.innerHTML = `<span class="text-red-400">Server Error.</span>`; } finally { btn.innerText = "RUN SYSTEMIC ANALYSIS"; btn.disabled = false; btn.classList.remove('opacity-50'); }
        }
    </script>
</body>
</html>
"""

def get_spatial_data():
    try:
        conn = sqlite3.connect('raw_data/spatial/atrric_macro.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT district, SUM(CAST(population AS REAL)) as total
            FROM population_data
            WHERE state = 'Selangor' AND (age = '15-19' OR age = '20-24') AND sex = 'both' AND ethnicity = 'overall'
            GROUP BY district ORDER BY total DESC LIMIT 4
        """)
        data = cursor.fetchall()
        conn.close()
        return {"labels": [r[0] for r in data], "values": [r[1] for r in data]}
    except: return {"labels": ["Error"], "values": [0]}

def get_news_data(limit=10):
    try:
        conn = sqlite3.connect('raw_data/news/atrric_news.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT published_date, level, title, matched_tags, content FROM news ORDER BY id DESC LIMIT {limit}")
        rows = cursor.fetchall()
        conn.close()
        return [{"date": r[0][:10], "level": r[1], "title": r[2], "tags": r[3], "content": r[4][:150] + "..." if r[4] else ""} for r in rows]
    except: return []

def get_news_level_data():
    try:
        conn = sqlite3.connect('raw_data/news/atrric_news.db')
        cursor = conn.cursor()
        cursor.execute("SELECT level, COUNT(*) FROM news GROUP BY level")
        data = cursor.fetchall()
        conn.close()
        return {"labels": [r[0] for r in data], "values": [r[1] for r in data]}
    except: return {"labels": ["Tiada Data"], "values": [0]}

def get_news_timeline():
    try:
        conn = sqlite3.connect('raw_data/news/atrric_news.db')
        cursor = conn.cursor()
        # Ambil 7 tarikh unik terakhir
        cursor.execute("""
            SELECT substr(published_date, 1, 10) as day, COUNT(*) 
            FROM news 
            GROUP BY day 
            ORDER BY day DESC LIMIT 7
        """)
        data = cursor.fetchall()
        conn.close()
        # Reverse supaya kronologi
        data = data[::-1] 
        return {"labels": [r[0] for r in data], "values": [r[1] for r in data]}
    except: return {"labels": ["Tiada"], "values": [0]}

@app.route('/')
def home(): return render_template_string(HTML_TEMPLATE)

@app.route('/api/spatial')
def api_spatial(): return jsonify(get_spatial_data())

@app.route('/api/news')
def api_news(): return jsonify(get_news_data())

@app.route('/api/news_level')
def api_news_level(): return jsonify(get_news_level_data())

@app.route('/api/news_timeline')
def api_news_timeline(): return jsonify(get_news_timeline())

@app.route('/api/synthesize', methods=['POST'])
def synthesize():
    if not ILMU_API_KEY: return jsonify({"error": "API Key tiada"})
    
    spatial = get_spatial_data()
    news = get_news_data(limit=3)

    spatial_text = "\n".join([f"- {spatial['labels'][i]}: {spatial['values'][i]} ribu Gen Z" for i in range(len(spatial['labels']))])
    news_text = "\n".join([f"- {n['title']}" for n in news])

    # Tarik RAG
    try:
        from core.rag import _get_rag
        rag = _get_rag()
        rag_results = rag.retrieve("pandangan gen z kos hidup kerja", limit=3)
        genz_quotes = "\n".join([f"- \"{getattr(r, 'text', str(r))[:150]}...\"" for r in rag_results])
    except: genz_quotes = "- Tiada data RAG."

    system_prompt = """Kau adalah Penganalisis Risiko Geopolitik & Sosio-Ekonomi. 
Buat analisis kausal (Causal Analysis) antara Trigger (Berita), Spatial (Kepadatan), dan Ground Truth (Komen). 
JANGAN ringkaskan berita. Terus bagi Insight tajam dalam 3 perenggan. Tiada mukadimah."""

    user_prompt = f"""
SPATIAL: \n{spatial_text}
TRIGGER (Berita): \n{news_text}
GROUND TRUTH (Komen Gen Z): \n{genz_quotes}

Tugasan: 3 perenggan analisis kausal.
P1: Trigger (Pilih 1 berita paling kritikal).
P2: Spatial Impact (Kaitkan dengan kepadatan Gen Z).
P3: Reality Check (Guna data Komen untuk tunjuk reaksi sebenar).
"""

    headers = {"Authorization": f"Bearer {ILMU_API_KEY}", "Content-Type": "application/json"}
    body = {"model": "ilmu/nemo-super", "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "max_tokens": 800, "temperature": 0.4}

    try:
        req = urllib.request.Request(ILMU_URL, data=json.dumps(body).encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as response:
            analysis = json.loads(response.read().decode('utf-8'))['choices'][0]['message']['content']
            return jsonify({"analysis": analysis})
    except Exception as e: return jsonify({"error": str(e)})

if __name__ == '__main__':
    print("=== COMMAND CENTER V3 RUNNING ===")
    app.run(host='127.0.0.1', port=5000, debug=False)
