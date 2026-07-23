from django.urls import path

from . import views




urlpatterns = [
    path('newsletter-preview/', views.newsletter_preview),
]
