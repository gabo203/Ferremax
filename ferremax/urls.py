from django.contrib import admin
from django.urls import include, path
from core import views as core_views
from django.conf import settings
from django.conf.urls.static import static
from api import views
urlpatterns = [
    path('', core_views.home, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('confirmacion_pago/', views.confirmacion_pago, name='confirmacion_pago'),
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)