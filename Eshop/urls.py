"""Root URL configuration for the Eshop storefront."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

handler404 = "brand.views.errors.not_found"
handler500 = "brand.views.errors.server_error"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("brand.urls")),
]

if settings.DEBUG:
    # In production the media directory is served by the web server, not Django.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
