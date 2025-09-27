from django.urls import path
from . import views


urlpatterns = [
    path("", views.health, name="health"),
    path("api/auth/request-otp", views.request_otp, name="request_otp"),
    path("api/auth/request-otp/", views.request_otp),
    path("api/auth/verify-otp", views.verify_otp, name="verify_otp"),
    path("api/auth/verify-otp/", views.verify_otp),
    path("api/auth/me", views.me, name="me"),
    path("api/auth/me/", views.me),
    path("api/email/invoice", views.email_invoice, name="email_invoice"),
    path("api/email/invoice/", views.email_invoice),
]
