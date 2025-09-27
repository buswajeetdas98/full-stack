import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# Import and expose the Django WSGI application
from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()

# Vercel serverless function handler
def handler(request):
    return app(request.environ, request.start_response)
