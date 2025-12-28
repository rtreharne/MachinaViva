from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.static import serve

urlpatterns = [
    # Add Django admin
    path('admin/', admin.site.urls),
    path("", include("tool.urls")),
]

# Serve static files locally (WhiteNoise handles production)
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
if settings.MEDIA_ROOT:
    urlpatterns += [
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
