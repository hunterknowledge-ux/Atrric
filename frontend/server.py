import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.rag import answer_question

PORT = 8000

def get_dashboard_data():
    # Baca summary.json (Data Analitik Gen Z)
    summary_path = os.path.join(_ROOT, "analytics_out", "summary.json")
    summary = {}
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

    # Data Spatial Mock (Untuk demo sidebar)
    spatial = [
        {"district": "Petaling", "population": 2500000},
        {"district": "Ulu Langat", "population": 1600000},
        {"district": "Klang", "population": 1200000},
        {"district": "Gombak", "population": 1000000},
        {"district": "Sepang", "population": 400000},
    ]

    # Data News Mock
    news = [
        {"title": "Rapid KL to deploy 85 shuttle buses at Sepang"},
        {"title": "Data Centre Bill to go to Cabinet"},
        {"title": "Sarawak targets 15,000MW power capacity"}
    ]

    return {"summary": summary, "spatial": spatial, "news": news}

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
    print(f"[Atrric] Python API running on :{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()