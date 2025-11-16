from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Add Django admin
    path('admin/', admin.site.urls),
    path("", include("tool.urls")),
]
