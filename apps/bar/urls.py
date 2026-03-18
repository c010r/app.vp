from django.urls import path
from . import views

app_name = 'bar'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('caja/<int:register_pk>/abrir/', views.open_session, name='open_session'),
    path('sesion/<int:session_pk>/cerrar/', views.close_session, name='close_session'),
    path('sesion/<int:session_pk>/pos/', views.pos, name='pos'),
    path('sesion/<int:session_pk>/venta/', views.create_sale, name='create_sale'),
    path('sesion/<int:session_pk>/resumen/', views.session_summary, name='session_summary'),
    # Admin productos
    path('productos/', views.product_list, name='product_list'),
    path('productos/nuevo/', views.product_create, name='product_create'),
    path('productos/<int:pk>/editar/', views.product_update, name='product_update'),
]
