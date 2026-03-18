from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    # Públicas (sin login)
    path('', views.public_event_list, name='public_list'),
    path('evento/<int:pk>/', views.public_event_detail, name='public_event_detail'),
    # Compra (requiere login)
    path('comprar/<int:ticket_type_id>/', views.purchase_ticket, name='purchase'),
    path('compra-exitosa/<int:pk>/', views.purchase_success, name='purchase_success'),
    # Cliente logueado
    path('mis-entradas/', views.my_tickets, name='my_tickets'),
    path('mis-entradas/<int:pk>/', views.my_ticket_detail, name='my_ticket_detail'),
    # Admin
    path('admin/eventos/', views.AdminEventListView.as_view(), name='admin_list'),
    path('admin/eventos/nuevo/', views.AdminEventCreateView.as_view(), name='event_create'),
    path('admin/eventos/<int:pk>/', views.admin_event_detail, name='admin_event_detail'),
    path('admin/eventos/<int:pk>/editar/', views.AdminEventUpdateView.as_view(), name='event_edit'),
    path('admin/eventos/<int:event_pk>/tipo-entrada/', views.ticket_type_create, name='ticket_type_create'),
    path('admin/tipo-entrada/<int:pk>/editar/', views.ticket_type_update, name='ticket_type_edit'),
    path('admin/entradas/', views.admin_ticket_list, name='admin_ticket_list'),
    path('admin/entradas/<int:pk>/usar/', views.mark_ticket_used, name='mark_used'),
    path('admin/checkin/', views.checkin_view, name='checkin'),
]
