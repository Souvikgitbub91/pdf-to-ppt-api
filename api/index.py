from http.server import BaseHTTPRequestHandler
import json
import requests
from io import BytesIO
import base64

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.path == '/health' or self.path == '/api/health':
            response = {
                "message": "PDF to PPT API is running", 
                "status": "active",
                "version": "1.0"
            }
        elif self.path == '/' or self.path == '/api':
            response = {
                "message": "PDF to PPT Conversion API",
                "endpoints": {
                    "GET /health": "Health check",
                    "POST /convert": "Convert PDF to PPT",
                    "POST /api/convert": "Convert PDF to PPT"
                }
            }
        else:
            response = {
                "error": "Endpoint not found",
                "available_endpoints": ["/health", "/convert"]
            }
            self.send_response(404)
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
        return

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            # Handle both /convert and /api/convert paths
            if self.path == '/convert' or self.path == '/api/convert':
                response = self.handle_convert(data)
                self.send_response(200)
            else:
                response = {
                    "success": False,
                    "error": "Endpoint not found. Use /convert or /api/convert"
                }
                self.send_response(404)
            
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {
                "success": False,
                "error": f"Internal server error: {str(e)}"
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

    def handle_convert(self, data):
        """Handle PDF to PPT conversion request"""
        try:
            if 'pdf_url' not in data:
                return {
                    "success": False,
                    "error": "Missing 'pdf_url' in request body"
                }
            
            pdf_url = data['pdf_url']
            
            # Validate URL
            if not pdf_url.startswith(('http://', 'https://')):
                return {
                    "success": False,
                    "error": "Invalid URL format"
                }
            
            # Download PDF (simplified - you can add actual conversion later)
            pdf_content = self.download_pdf(pdf_url)
            
            if pdf_content:
                # For now, return success message without actual conversion
                # You can integrate python-pptx later
                return {
                    "success": True,
                    "message": "PDF received successfully - Conversion service ready",
                    "file_size": len(pdf_content),
                    "next_step": "Integrate python-pptx for actual conversion",
                    "conversion_id": f"conv_{hash(pdf_url) % 10000}",
                    "status": "file_received"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to download PDF from the provided URL"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Conversion error: {str(e)}"
            }

    def download_pdf(self, pdf_url):
        """Download PDF from URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(pdf_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Basic PDF validation
            if response.content.startswith(b'%PDF'):
                return response.content
            return None
            
        except Exception as e:
            print(f"PDF download error: {e}")
            return None

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()