# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('descargar/', views.descargar_excel, name='descargar_excel'),
]