from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'get_full_name', 'role', 'phone', 'is_active_staff', 'is_active')
    list_filter = ('role', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Hospital Role', {'fields': ('role', 'phone', 'is_active_staff')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Hospital Role', {'fields': ('role', 'phone')}),
    )
