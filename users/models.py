from django.contrib.auth.models import AbstractUser
from django.db import models

import uuid
from django.utils import timezone
from datetime import timedelta

# Create your models here.


class User(AbstractUser):
    # Email as unique identifier for login
    email = models.EmailField(unique=True)

    # Profile picture for each user
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    # Short biography
    bio = models.TextField(max_length=500, blank=True)

    # Date of birth
    date_of_birth = models.DateField(null=True, blank=True)

    # Gender options
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)

    # Account privacy
    is_private_account = models.BooleanField(default=False)

    is_log_in = models.BooleanField(default=False)  # Tracks if user is currently logged in

    # User creation timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    # Email verification check
    is_email_verified = models.BooleanField(default=False)

    # Use email as login field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Username still required for superuser

    def __str__(self):
        return self.email

class EmailVerificationOTP(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_otps")
    otp = models.CharField(max_length=6)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at