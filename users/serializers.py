from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password2', 'profile_picture', 'bio', 'date_of_birth', 'gender')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            bio=validated_data.get('bio', ''),
            date_of_birth=validated_data.get('date_of_birth'),
            gender=validated_data.get('gender', ''),
            profile_picture=validated_data.get('profile_picture')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

# Serializer for login
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        # Use Django's authenticate method to verify credentials
        user = authenticate(email=attrs['email'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError("Invalid email or password")

        # Block unverified users
        if not user.is_email_verified:
            raise serializers.ValidationError("Email not verified. Please check your inbox.")

        attrs['user'] = user
        return attrs

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'bio',
            'gender',
            'profile_picture',
            'is_log_in',
            'is_email_verified'
        )

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        from users.models import User, EmailVerificationOTP

        try:
            user = User.objects.get(email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email")

        try:
            otp_obj = EmailVerificationOTP.objects.filter(user=user, otp=attrs['otp']).latest('created_at')
        except EmailVerificationOTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP")

        if otp_obj.is_expired():
            raise serializers.ValidationError("OTP expired")

        # OTP is valid → mark as used
        otp_obj.delete()

        attrs['user'] = user
        return attrs