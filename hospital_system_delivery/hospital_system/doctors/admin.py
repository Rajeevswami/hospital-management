from django.contrib import admin
from .models import Doctor

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'experience_years', 'consultation_fee', 'is_active')
    list_filter = ('specialization', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'specialization')
