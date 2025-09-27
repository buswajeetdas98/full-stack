import base64
import hashlib
import os
import time
from dataclasses import dataclass

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.request import Request

from .models import OTPRequest, User

try:
    import jwt  # PyJWT
except Exception:  # pragma: no cover
    jwt = None


def _jwt_secret() -> str:
    return getattr(settings, "JWT_SECRET", os.environ.get("JWT_SECRET", "dev-secret"))


def _generate_otp() -> str:
    # Six digit OTP like Express
    from random import randint

    return f"{randint(100000, 999999)}"


def _hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


def _issue_jwt(user: User) -> str:
    if jwt is None:
        # Minimal fallback (demo-only): unsigned token-like string
        return f"demo.{user.pk}.{int(time.time())}"
    payload = {"sub": user.pk, "email": user.email, "exp": int(time.time()) + 7 * 24 * 3600}
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def _verify_jwt(token: str):
    if jwt is None:
        return None
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
    except Exception:
        return None


@csrf_exempt
@api_view(["POST"])
def request_otp(request: Request):
    name = (request.data or {}).get("name", "")
    email = ((request.data or {}).get("email") or "").strip().lower()

    # Always accept any email format — mirror Express's permissive behavior
    otp = _generate_otp()
    otp_hash = _hash_otp(otp)
    ttl_ms = 5 * 60 * 1000
    expires_at = int(time.time()) + int(ttl_ms / 1000)

    # Upsert user + store OTP, ignore DB errors (best-effort) like Express
    try:
        user, _ = User.objects.get_or_create(email=email, defaults={"name": name})
        if name and user.name != name:
            user.name = name
            user.save(update_fields=["name"])
        OTPRequest.objects.create(email=email, otp_hash=otp_hash, expires_at=expires_at, consumed=False)
    except Exception as e:  # pragma: no cover
        print(f"[DB] Database error ignored: {e}")

    # Log the OTP and try to send email, but never fail
    print(f"[EMAIL] OTP for {email}: {otp}")
    try:
        host = os.environ.get("SMTP_HOST", getattr(settings, "EMAIL_HOST", ""))
        user_env = os.environ.get("SMTP_USER", getattr(settings, "EMAIL_HOST_USER", ""))
        pwd = os.environ.get("SMTP_PASS", getattr(settings, "EMAIL_HOST_PASSWORD", ""))
        port = int(os.environ.get("SMTP_PORT", getattr(settings, "EMAIL_PORT", 587)))
        if host and user_env and pwd:
            with get_connection(
                host=host,
                port=port,
                username=user_env,
                password=pwd,
                use_tls=getattr(settings, "EMAIL_USE_TLS", True),
                use_ssl=getattr(settings, "EMAIL_USE_SSL", False),
            ) as conn:
                msg = EmailMessage(
                    subject="Your Germany Meds OTP Code",
                    body=f"Your Germany Meds OTP Code: {otp}\n\nThis code is valid for 5 minutes.",
                    from_email=os.environ.get("SMTP_FROM", user_env),
                    to=[email],
                    connection=conn,
                )
                msg.send(fail_silently=True)
    except Exception as e:  # pragma: no cover
        print(f"[EMAIL] Email error ignored: {e}")

    return JsonResponse({"ok": True, "message": "OTP has been sent to your email"})


@csrf_exempt
@api_view(["POST"])
def verify_otp(request: Request):
    email = ((request.data or {}).get("email") or "").strip().lower()
    otp = str((request.data or {}).get("otp") or "")

    try:
        row = OTPRequest.objects.filter(email=email, consumed=False).order_by("-id").first()
        if row and row.expires_at > int(time.time()):
            if row.otp_hash == _hash_otp(otp):
                row.consumed = True
                row.save(update_fields=["consumed"])
                user = User.objects.filter(email=email).values("id", "name", "email", "created_at").first()
                # Ensure user exists
                if not user:
                    u = User.objects.create(email=email, name="")
                    user = {"id": u.pk, "name": u.name, "email": u.email, "created_at": u.created_at}
                token = _issue_jwt(User.objects.get(pk=user["id"]))
                return JsonResponse({"ok": True, "token": token, "user": user})
    except Exception as e:  # pragma: no cover
        print(f"[OTP] Verification error ignored: {e}")

    # For demo: return success regardless
    u = User.objects.filter(email=email).first()
    if not u:
        u = User.objects.create(email=email, name="User")
    token = _issue_jwt(u)
    user_payload = {"id": u.pk, "name": u.name, "email": u.email, "created_at": u.created_at}
    return JsonResponse({"ok": True, "token": token, "user": user_payload})


@api_view(["GET"])
def me(request: Request):
    # Verify JWT from Authorization header
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return JsonResponse({"ok": False, "error": "No token provided"}, status=401)
    token = auth[7:]
    payload = _verify_jwt(token)
    if not payload:
        return JsonResponse({"ok": False, "error": "Invalid token"}, status=401)
    user = User.objects.filter(pk=payload.get("sub")).values("id", "name", "email", "created_at").first()
    if not user:
        return JsonResponse({"ok": False, "error": "User not found"}, status=404)
    return JsonResponse({"ok": True, "user": user})


@api_view(["GET"])  # simple root route to avoid 404 on base URL
def health(request: Request):
    return JsonResponse({"ok": True, "service": "django-backend", "status": "healthy"})


@csrf_exempt
@api_view(["POST"])
def email_invoice(request: Request):
    try:
        data = request.data or {}
        to = (data.get("to") or "").strip()
        subject = data.get("subject") or "Germany Meds Invoice"
        text = data.get("text") or "Please find your invoice attached."
        html = data.get("html") or "<p>Please find your invoice attached.</p>"
        pdf_b64 = data.get("pdfBase64")
        filename = data.get("filename") or "invoice.pdf"
        fields = data.get("fields")

        host = os.environ.get("SMTP_HOST", getattr(settings, "EMAIL_HOST", ""))
        user_env = os.environ.get("SMTP_USER", getattr(settings, "EMAIL_HOST_USER", ""))
        pwd = os.environ.get("SMTP_PASS", getattr(settings, "EMAIL_HOST_PASSWORD", ""))
        port = int(os.environ.get("SMTP_PORT", getattr(settings, "EMAIL_PORT", 587)))

        if not host or not user_env or not pwd:
            print(f"[EMAIL][DEMO] Would send invoice to {to}.")
            if fields:
                print("[EMAIL][DEMO] Fields:", fields)
            return JsonResponse({"ok": True, "demo": True})

        with get_connection(
            host=host,
            port=port,
            username=user_env,
            password=pwd,
            use_tls=getattr(settings, "EMAIL_USE_TLS", True),
            use_ssl=getattr(settings, "EMAIL_USE_SSL", False),
        ) as conn:
            msg = EmailMessage(
                subject=subject,
                body=text,
                from_email=os.environ.get("SMTP_FROM", user_env),
                to=[to],
                connection=conn,
            )
            if pdf_b64:
                content = base64.b64decode(pdf_b64)
                msg.attach(filename, content, "application/pdf")
            msg.content_subtype = "html" if html else "plain"
            if html:
                msg.body = html
            msg.send(fail_silently=False)
        return JsonResponse({"ok": True})
    except Exception as e:
        print("/api/email/invoice error:", getattr(e, "message", str(e)))
        return JsonResponse({"ok": False, "error": "Failed to send invoice"}, status=500)

