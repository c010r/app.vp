from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('nuevo/', views.product_create, name='product_create'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('<int:pk>/editar/', views.product_update, name='product_update'),
    path('<int:pk>/movimiento/', views.stock_movement, name='stock_movement'),
    path('movimientos/', views.movement_list, name='movement_list'),
]
