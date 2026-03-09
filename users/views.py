from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from users.serializers import RegisterSerializer, LoginSerializer, UserListSerializer, VerifyOTPSerializer
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from django.utils.http import urlsafe_base64_decode

from users.utils import send_verification_email
from users.tokens import email_verification_token

# Create your views here.

User = get_user_model()

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():

            # Create the user
            user = serializer.save()

            # Send verification email
            send_verification_email(user, request)

            # Return a Response — DO NOT issue JWT yet
            return Response({
                "message": "Registration successful. Please verify your email.",
                "email": user.email
            }, status=status.HTTP_201_CREATED)

        # Validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Mark user as logged in
            user.is_log_in = True
            user.save(update_fields=['is_log_in'])

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access = str(refresh.access_token)

            return Response({
                "user": {
                    "email": user.email,
                    "username": user.username,
                    "bio": user.bio,
                    "gender": user.gender,
                    "profile_picture": user.profile_picture.url if user.profile_picture else None,
                    "is_log_in": user.is_log_in,
                },
                "refresh": str(refresh),
                "access": access
            }, status=status.HTTP_200_OK)

        # Return validation errors if credentials invalid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserListView(APIView):
    permission_classes = [permissions.IsAdminUser]  # Only staff users can access

    def get(self, request):
        # Get all users
        users = User.objects.all()
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # Only logged-in users can logout

    def post(self, request):
        user = request.user

        # Mark user as logged out
        user.is_log_in = False
        user.save(update_fields=['is_log_in'])

        # Blacklist refresh token (optional)
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception as e:
                return Response({"detail": "Invalid refresh token"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "Logged out successfully"}, status=status.HTTP_200_OK)

class VerifyEmailView(APIView):

    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({"error": "Invalid verification link"}, status=400)

        if email_verification_token.check_token(user, token):
            if user.is_email_verified:
                return Response({"message": "Email already verified"})
            user.is_email_verified = True
            user.save(update_fields=['is_email_verified'])
            return Response({"message": "Email verified successfully"})
        else:
            return Response({"error": "Invalid or expired token"}, status=400)

class VerifyOTPView(APIView):

    # Endpoint to verify OTP sent to user's email.

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Mark user as email verified
            user.is_email_verified = True
            user.save(update_fields=['is_email_verified'])

            return Response({
                "message": "Email verified successfully. You can now log in.",
                "email": user.email
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)