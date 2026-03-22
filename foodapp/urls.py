from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Main app
    path('', include('main.urls')),

    # Accounts app
    path('accounts/', include('accounts.urls')),

    # API routes
    path('api/accounts/', include('accounts.api_urls')),
    path('api/', include('main.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)