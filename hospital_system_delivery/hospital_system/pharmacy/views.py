from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from core.decorators import role_required
from .models import Medicine, Prescription
from .forms import MedicineForm, PrescriptionForm, PrescriptionItemFormSet


@login_required
def medicine_list(request):
    medicines = Medicine.objects.all()
    return render(request, 'pharmacy/medicine_list.html', {'medicines': medicines})


@login_required
@role_required('ADMIN', 'PHARMACIST')
def medicine_create(request):
    form = MedicineForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Medicine added to inventory.')
        return redirect('pharmacy:medicine_list')
    return render(request, 'pharmacy/medicine_form.html', {'form': form, 'title': 'Add Medicine'})


@login_required
@role_required('ADMIN', 'PHARMACIST')
def medicine_update(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    form = MedicineForm(request.POST or None, instance=medicine)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Stock updated.')
        return redirect('pharmacy:medicine_list')
    return render(request, 'pharmacy/medicine_form.html', {'form': form, 'title': f'Edit {medicine.name}'})


@login_required
def prescription_list(request):
    prescriptions = Prescription.objects.select_related('patient', 'doctor__user').prefetch_related('items__medicine')
    return render(request, 'pharmacy/prescription_list.html', {'prescriptions': prescriptions})


@login_required
@role_required('ADMIN', 'DOCTOR', 'PHARMACIST')
def prescription_create(request):
    form = PrescriptionForm(request.POST or None)
    formset = PrescriptionItemFormSet(request.POST or None)

    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        try:
            with transaction.atomic():
                prescription = form.save(commit=False)
                prescription.created_by = request.user
                prescription.save()

                formset.instance = prescription
                items = formset.save(commit=False)
                for item in items:
                    # Lock the medicine row so two prescriptions can't both deduct
                    # from the same stock count at the same instant (oversell bug).
                    medicine = Medicine.objects.select_for_update().get(pk=item.medicine_id)
                    if item.quantity > medicine.stock_quantity:
                        raise ValueError(f"Only {medicine.stock_quantity} units of {medicine.name} left.")
                    medicine.stock_quantity -= item.quantity
                    medicine.save()
                    item.prescription = prescription
                    item.save()
                for obj in formset.deleted_objects:
                    obj.delete()

            messages.success(request, 'Prescription created and stock updated.')
            return redirect('pharmacy:prescription_list')
        except ValueError as e:
            messages.error(request, str(e))

    return render(request, 'pharmacy/prescription_form.html', {'form': form, 'formset': formset})
