
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('analytics/', include('analytics.urls')),
    path('api/', include('api.urls')),
    path('core/', include('core.urls')),
    path('dashbaord/', include('dashboard.urls')),
]
