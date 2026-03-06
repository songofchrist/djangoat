from django.urls import path

from . import views


urlpatterns = [
    path('utils/', views.utils),
    path('template-tags/', views.template_tags),
]
