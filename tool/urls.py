from django.urls import path
from . import views

urlpatterns = [
    path("", views.index),
    path("login/", views.lti_login),
    path("launch/", views.lti_launch),
    path("jwks/", views.jwks),
    path("landing/", views.landing),
    path("test_set/", views.test_set_cookie),
    path("test_read/", views.test_read_cookie),
]
