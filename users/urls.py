from django.urls import path
from users.views import RegisterView, LoginView, UserListView, LogoutView, VerifyEmailView, VerifyOTPView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('list/', UserListView.as_view(), name='user-list'),    # staff-only endpoint
    path('logout/', LogoutView.as_view(), name='logout'),
    path("verify-email/<uidb64>/<token>/", VerifyEmailView.as_view(), name="email-verify"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
]