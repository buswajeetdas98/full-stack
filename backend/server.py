import os

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

# Expose WSGI application as `app` for Vercel Python runtime
from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()
