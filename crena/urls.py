
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('accounts/', include('allauth.urls')), # Path for the allauth and configs

    path('admin/', admin.site.urls),
    path('analytics/', include('analytics.urls')),
    path('api/', include('api.urls')),
    path('core/', include('core.urls')),
    path('dashbaord/', include('dashboard.urls')),
]
