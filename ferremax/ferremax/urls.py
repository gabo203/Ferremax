from django.contrib import admin
from django.urls import path, include
from api.views import home, productos, CarritoViewSet, WebpayPlusCreate, CommitWebpayTransaction

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('productos/', productos, name='productos'),
    path('api/', include('api.urls')),
    path('api/carrito/<int:pk>/', CarritoViewSet.as_view({'get': 'retrieve'}), name='carrito'),
    path('api/carrito/', CarritoViewSet.as_view({'post': 'create'}), name='crear_carrito'),
    path('api/carrito/<int:pk>/add/', CarritoViewSet.as_view({'post': 'add_item'}), name='agregar_item_carrito'),
    path("webpay-plus/create/<int:carrito_id>/", WebpayPlusCreate.as_view(), name="webpay-plus-create"),
    path("webpay-plus/commit/", CommitWebpayTransaction.as_view(), name="webpay-plus-commit"),
]
