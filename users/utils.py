import random

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from users.models import EmailVerificationOTP
from users.tokens import email_verification_token


def generate_otp(length=6):

    # Generates a numeric OTP of given length
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def send_verification_email(user, request):
    # 1 Generate token for link
    token = email_verification_token.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    verification_link = request.build_absolute_uri(
        reverse('email-verify', kwargs={'uidb64': uid, 'token': token})
    )

    # 2 Generate OTP
    otp = generate_otp()

    # Save OTP in database
    EmailVerificationOTP.objects.create(user=user, otp=otp)

    # 3 Email subject and message
    subject = "Verify Your Email Address"
    message = f"""
    Hi {user.username},

    Please verify your email to complete registration.

    🔗 Verification Link: {verification_link}
    🔢 OTP: {otp}

    This link and OTP expire in 10 minutes.

    Thank you!
    """

    # 4 Send email via SMTP
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,  # e.g., "youremail@gmail.com"
        [user.email],
        fail_silently=False,
    )