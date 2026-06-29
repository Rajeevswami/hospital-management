from django.contrib import admin
from .models import Ward, Bed, Admission

class BedInline(admin.TabularInline):
    model = Bed
    extra = 1

@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ('name', 'ward_type', 'charge_per_day')
    inlines = [BedInline]

@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ('ward', 'bed_number', 'is_occupied')
    list_filter = ('ward', 'is_occupied')

@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'diagnosis', 'doctor', 'bed', 'admission_date', 'status')
    list_filter = ('status',)
    search_fields = ('patient__patient_id', 'patient__first_name', 'diagnosis')
