from django.urls import path
from users.views import RegisterView, LoginView, UserListView, LogoutView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),          # login endpoint
    path('list/', UserListView.as_view(), name='user-list'),    # staff-only endpoint
    path('logout/', LogoutView.as_view(), name='logout'),
]