from django.urls import path, include
from rest_framework import routers
from .views import ProductoViewSet, WebpayPlusCreate, CommitWebpayTransaction, carrito, eliminar_item_carrito

router = routers.DefaultRouter()
router.register(r'productos', ProductoViewSet, basename='Producto')

urlpatterns = [
    path('', include(router.urls)),
    path('productos/name/<str:nombre>/', ProductoViewSet.as_view({'get': 'retrieve_by_name'}), name='producto_by_name'),
    path('productos/id/<int:pk>/', ProductoViewSet.as_view({'get': 'retrieve'}), name='producto_by_id'),
    path("webpay-plus/create/<int:producto_id>/", WebpayPlusCreate.as_view(), name="webpay-plus-create"),
    path("webpay-plus/commit/", CommitWebpayTransaction.as_view(), name="webpay-plus-commit"),
    path('carrito/', carrito, name='carrito'),
    path('carrito/eliminar/<int:item_id>/', eliminar_item_carrito, name='eliminar_item_carrito'),
]

urlpatterns += router.urls
