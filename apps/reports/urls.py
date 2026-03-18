from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('entradas/', views.tickets_report, name='tickets'),
    path('barra/', views.bar_report, name='bar'),
    path('inventario/', views.inventory_report, name='inventory'),
]
