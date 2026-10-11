import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Tambah parent dir ke sys.path supaya `from core.rag import ...` jalan
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.rag import answer_question

PORT = 8000


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
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            super().do_GET()

    def log_message(self, fmt, *args):
        pass  # senyapkan log request


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f"[Atrric] http://localhost:{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()