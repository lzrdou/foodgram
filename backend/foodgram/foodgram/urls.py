from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("api/", include("api.urls", namespace="api")),
    path('admin/', include(admin.site.urls)),
]
