import json
import os
import sys
import sqlite3
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.rag import answer_question

PORT = 8000
REPORTS_DIR = "reports"

if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

def get_spatial_data():
    try:
        conn = sqlite3.connect('spatial_cache.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, name, type, lat, lon FROM real_projects")
        projects = [dict(row) for row in c.fetchall()]
        conn.close()
        return projects
    except Exception as e: return []

def get_analytics_data():
    try:
        conn = sqlite3.connect('spatial_cache.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT date, sector, ipi_index FROM ipi_stats ORDER BY date ASC")
        ipi = [dict(row) for row in c.fetchall()]
        conn.close()
        return {"ipi": ipi}
    except Exception as e: return {"ipi": []}

def get_news_data():
    try:
        conn = sqlite3.connect('spatial_cache.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, title, link, source, country, lat, lon, date, description FROM live_news ORDER BY date DESC")
        news = [dict(row) for row in c.fetchall()]
        conn.close()
        return news
    except Exception as e: return []

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/query":
            q = parse_qs(parsed.query).get("q", [""])[0].strip()
            if not q:
                data = {"error": "empty query", "answer": "", "sources": []}
            else:
                try: data = answer_question(q)
                except Exception as e: data = {"error": str(e), "answer": "", "sources": []}
            self._send_json(data)
        elif parsed.path == "/api/spatial":
            self._send_json({"type": "geojson", "data": get_spatial_data()})
        elif parsed.path == "/api/analytics":
            self._send_json(get_analytics_data())
        elif parsed.path == "/api/news":
            self._send_json({"data": get_news_data()})
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/analyze":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data.decode('utf-8'))
            
            title = payload.get("title", "Unknown News")
            source = payload.get("source", "Unknown")
            description = payload.get("description", "No description.")
            template = payload.get("template", "General Impact")
            
            # Prompt ringkas untuk core.rag kau
            prompt = f"""
            TUGASAN ANALISA RISIKAN:
            Berita: "{title}"
            Sumber: {source}
            Ringkasan: {description}
            
            Arahan: Buat analisa '{template}' mengaitkan berita ini dengan data Gen Z Malaysia.
            Format output: Markdown dengan bahagian Analysis dan Recommendation.
            """
            
            try:
                # Panggil RAG pipeline kau
                result = answer_question(prompt)
                answer = result.get("answer", "Tiada jawapan dari LLM.")
                
                # Auto-Save
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                safe_title = "".join([c for c in title if c.isalpha() or c.isspace()])[:30].replace(" ", "_")
                filename = f"{REPORTS_DIR}/INTEL_{timestamp}_{safe_title}.md"
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"# INTEL REPORT: {title}\n")
                    f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}\n")
                    f.write(f"**Source:** {source}\n")
                    f.write(f"**Template:** {template}\n\n")
                    f.write(f"**Original Context:** {description}\n\n---\n\n")
                    f.write(answer)
                
                self._send_json({"status": "success", "answer": answer, "file": filename})
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)})
        else:
            self.send_response(404)
            self.end_headers()

    def _send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args): pass

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"[Atrric] Python API + DB running on :{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()