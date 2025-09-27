from http.server import BaseHTTPRequestHandler
import json
import os
import jwt
import time

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Get request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            email = data.get("email", "").strip().lower()
            otp = data.get("otp", "").strip()
            
            if not email or not otp:
                self.send_error_response({"ok": False, "error": "Email and OTP are required"})
                return
            
            # For demo purposes, accept any 6-digit OTP
            if len(otp) == 6 and otp.isdigit():
                # Generate JWT token
                jwt_secret = os.environ.get('JWT_SECRET', 'dev-secret')
                payload = {
                    "sub": email,
                    "email": email,
                    "exp": int(time.time()) + 7 * 24 * 3600  # 7 days
                }
                
                try:
                    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
                except:
                    # Fallback for demo
                    token = f"demo.{email}.{int(time.time())}"
                
                user_data = {
                    "id": email,
                    "name": "User",
                    "email": email,
                    "created_at": time.time()
                }
                
                self.send_success_response({
                    "ok": True,
                    "token": token,
                    "user": user_data
                })
            else:
                self.send_error_response({"ok": False, "error": "Invalid OTP"})
                
        except Exception as e:
            print(f"Error in verify-otp: {e}")
            self.send_error_response({"ok": False, "error": "Failed to verify OTP"})
    
    def send_success_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def send_error_response(self, data):
        self.send_response(400)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
