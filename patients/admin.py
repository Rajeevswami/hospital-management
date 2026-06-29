from django.contrib import admin
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'full_name', 'age', 'gender', 'phone', 'blood_group', 'created_at')
    search_fields = ('patient_id', 'first_name', 'last_name', 'phone')
    list_filter = ('gender', 'blood_group')
    readonly_fields = ('patient_id',)
