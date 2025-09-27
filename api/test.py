from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "message": "Simple test endpoint working!",
            "timestamp": "2025-09-27T09:53:00Z",
            "status": "success"
        }
        
        self.wfile.write(json.dumps(response).encode())
