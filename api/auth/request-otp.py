"""
Request OTP API
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import hashlib
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from random import randint

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
            
            name = data.get("name", "")
            email = data.get("email", "").strip().lower()
            
            if not email:
                self.send_error_response({"ok": False, "error": "Email is required"})
                return
            
            # Generate OTP
            otp = f"{randint(100000, 999999)}"
            
            # Send email
            success = self.send_otp_email(email, otp)
            
            if success:
                self.send_success_response({
                    "ok": True,
                    "message": "OTP has been sent to your email"
                })
            else:
                self.send_success_response({
                    "ok": True,
                    "message": "OTP has been sent to your email (demo mode)"
                })
                
        except Exception as e:
            print(f"Error in request-otp: {e}")
            self.send_error_response({"ok": False, "error": "Failed to send OTP"})
    
    def send_otp_email(self, email, otp):
        try:
            # Get SMTP settings from environment
            smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.environ.get('SMTP_PORT', '465'))
            smtp_user = os.environ.get('SMTP_USER', '')
            smtp_pass = os.environ.get('SMTP_PASS', '')
            smtp_from = os.environ.get('SMTP_FROM', smtp_user)
            
            if not smtp_user or not smtp_pass:
                print(f"[EMAIL][DEMO] Would send OTP {otp} to {email}")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_from
            msg['To'] = email
            msg['Subject'] = "Your Germany Meds OTP Code"
            
            body = f"Your Germany Meds OTP Code: {otp}\n\nThis code is valid for 5 minutes."
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port)
                server.starttls()
            
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            
            print(f"[EMAIL] OTP {otp} sent to {email}")
            return True
            
        except Exception as e:
            print(f"[EMAIL] Error sending email: {e}")
            return False
    
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
