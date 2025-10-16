from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "message": "PDF to PPT API is running",
            "status": "active",
            "endpoints": {
                "GET /health": "Health check",
                "POST /api/convert": "Convert PDF to PPT"
            }
        }
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
        return