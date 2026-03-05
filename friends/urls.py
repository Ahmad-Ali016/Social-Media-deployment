from django.urls import path
from friends.views import SendFriendRequestView, FriendListView, FriendRequestActionView, PendingFriendRequestsView, \
    UnfriendView

urlpatterns = [
    path('send/<str:username>/', SendFriendRequestView.as_view(), name='send-friend-request'),
    path('list/', FriendListView.as_view(), name='friend-list'),
    path("request/<int:request_id>/", FriendRequestActionView.as_view(), name="friend-request-action"),
    path('requests/', PendingFriendRequestsView.as_view(), name='pending-requests'),
    path('unfriend/<str:username>/', UnfriendView.as_view(), name='unfriend'),
]