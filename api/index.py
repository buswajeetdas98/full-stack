from http.server import BaseHTTPRequestHandler
import sys
import os
import json

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# Import Django
import django
django.setup()

from django.core.handlers.wsgi import WSGIHandler
from django.http import JsonResponse
from django.urls import resolve
from django.conf import settings

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Health check endpoint
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {"ok": True, "service": "django-backend", "status": "healthy"}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"error": "Not found"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        # Handle POST requests - you can add your API logic here
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = {"message": "POST endpoint working"}
        self.wfile.write(json.dumps(response).encode())
