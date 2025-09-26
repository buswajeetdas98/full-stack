from django.db import models


class User(models.Model):
    name = models.CharField(max_length=255, blank=True, default="")
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=32, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.email or self.phone or f"User {self.pk}"


class OTPRequest(models.Model):
    phone = models.CharField(max_length=32, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    otp_hash = models.CharField(max_length=128)
    expires_at = models.BigIntegerField()  # unix seconds, to mirror Express
    consumed = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["email", "consumed", "id"]),
        ]


# Create your models here.
