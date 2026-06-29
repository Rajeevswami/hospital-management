from django.contrib import admin
from .models import Medicine, Prescription, PrescriptionItem

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'manufacturer', 'unit_price', 'stock_quantity', 'reorder_level', 'expiry_date')
    search_fields = ('name', 'manufacturer')

class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'created_at')
    inlines = [PrescriptionItemInline]
