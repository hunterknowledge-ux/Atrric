import json
import os
import sys
import sqlite3
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.rag import answer_question

PORT = 8000

def get_dashboard_data():
    summary_path = os.path.join(_ROOT, "analytics_out", "summary.json")
    summary = {}
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

    spatial = [
        {"district": "Petaling", "population": 2500000},
        {"district": "Ulu Langat", "population": 1600000},
        {"district": "Klang", "population": 1200000},
        {"district": "Gombak", "population": 1000000},
        {"district": "Sepang", "population": 400000},
    ]

    news = [
        {"title": "Rapid KL to deploy 85 shuttle buses at Sepang"},
        {"title": "Data Centre Bill to go to Cabinet"},
        {"title": "Sarawak targets 15,000MW power capacity"}
    ]

    return {"summary": summary, "spatial": spatial, "news": news}

def get_spatial_data():
    try:
        conn = sqlite3.connect('spatial_cache.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, name, type, lat, lon FROM real_projects")
        projects = [dict(row) for row in c.fetchall()]
        conn.close()
        return projects
    except Exception as e:
        print("Spatial DB Error:", e)
        return []

def get_analytics_data():
    try:
        conn = sqlite3.connect('spatial_cache.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT date, sector, ipi_index FROM ipi_stats ORDER BY date ASC")
        ipi = [dict(row) for row in c.fetchall()]
        
        c.execute("SELECT state, projects, investment FROM mida_stats")
        mida = [dict(row) for row in c.fetchall()]
        
        conn.close()
        return {"ipi": ipi, "mida": mida}
    except Exception as e:
        print("Analytics DB Error:", e)
        return {"ipi": [], "mida": []}

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
            self._send_json(get_dashboard_data())
            
        elif parsed.path == "/api/spatial":
            self._send_json({"type": "geojson", "data": get_spatial_data()})
            
        elif parsed.path == "/api/analytics":
            self._send_json(get_analytics_data())
            
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
    print(f"[Atrric] Python API + DB running on :{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()