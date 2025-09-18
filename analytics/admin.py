from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Session, Hit


admin.site.register(Session)
admin.site.register(Hit)