from django.urls import path
from . import views

urlpatterns = [
    path('productos/', views.producto_list, name='producto_list'),
    path('agregar-al-carrito/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('eliminar-del-carrito/<int:producto_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('carrito/', views.carrito, name='carrito'),
    path('procesar_compra/', views.procesar_compra, name='procesar_compra'),
    path('contacto/', views.contacto, name='contacto'),
    path('producto/<int:producto_id>/', views.producto_detalle, name='producto_detalle'),
]