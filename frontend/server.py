import json
import os
import sys
import sqlite3
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# Cuba import fungsi kau (Pastikan nama fungsi betul)
try:
    from core.rag import answer_question
except ImportError:
    def answer_question(q): return {"error": "core.rag not found", "answer": "", "sources": []}

def get_dashboard_data():
    # 1. Baca summary.json (dari analytics/write.py)
    summary_path = os.path.join(_ROOT, "analytics_out", "summary.json")
    summary = {}
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

    # 2. Baca SQLite News & Spatial (dari report/generate.py)
    spatial_data = []
    news_data = []
    
    try:
        db_spatial = os.path.join(_ROOT, "raw_data/spatial/atrric_macro.db")
        conn = sqlite3.connect(db_spatial)
        cur = conn.cursor()
        cur.execute("SELECT district, SUM(CAST(population AS REAL)) as total FROM population_data WHERE state = 'Selangor' AND (age = '15-19' OR age = '20-24') AND sex = 'both' AND ethnicity = 'overall' GROUP BY district ORDER BY total DESC LIMIT 5")
        spatial_data = [{"district": r[0], "population": r[1]} for r in cur.fetchall()]
        conn.close()
    except Exception as e:
        pass

    try:
        db_news = os.path.join(_ROOT, "raw_data/news/atrric_news.db")
        conn = sqlite3.connect(db_news)
        cur = conn.cursor()
        cur.execute("SELECT title FROM news ORDER BY id DESC LIMIT 5")
        news_data = [{"title": r[0]} for r in cur.fetchall()]
        conn.close()
    except Exception as e:
        pass

    return {"summary": summary, "spatial": spatial_data, "news": news_data}


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/api/query":
            q = parse_qs(parsed.query).get("q", [""])[0].strip()
            if not q:
                data = {"error": "empty query", "answer": "", "sources": []}
            else:
                try:
                    data = answer_question(q)
                except Exception as e:
                    data = {"error": str(e), "answer": "", "sources": []}
            self._send_json(data)

        elif parsed.path == "/api/dashboard":
            # Hantar data penuh dashboard
            data = get_dashboard_data()
            self._send_json(data)

        else:
            super().do_GET()

    def _send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"[Atrric] http://localhost:8000")
    HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()