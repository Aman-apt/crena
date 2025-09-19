from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Service, User


class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Extra fields", {"fields": ("api_token",)}),
    )


admin.site.register(User, UserAdmin)



class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "link", "owner", "statuses")
    list_display_links = ("name",)
    list_filter = ("statuses",)
    search_fields = ("name", "link", "owner")


admin.site.register(Service, ServiceAdmin)