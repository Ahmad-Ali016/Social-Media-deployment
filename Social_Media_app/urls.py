from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.http import HttpResponse

urlpatterns = [
    path('', lambda request: HttpResponse("Social Media App is Live 🚀")),
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/profiles/', include('profiles.urls')),
    path('api/friends/', include('friends.urls')),
    path('api/posts/', include('posts.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

