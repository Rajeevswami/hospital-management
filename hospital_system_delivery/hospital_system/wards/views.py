from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.utils import timezone
from core.decorators import role_required
from .models import Admission, Bed, Ward
from .forms import AdmissionForm, DischargeForm


@login_required
def admission_list(request):
    admissions = Admission.objects.select_related('patient', 'doctor__user', 'bed__ward').filter(status='ADMITTED')
    return render(request, 'wards/admission_list.html', {'admissions': admissions})


@login_required
@role_required('ADMIN', 'RECEPTIONIST', 'DOCTOR')
def admission_create(request):
    form = AdmissionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            admission = form.save(commit=False)
            admission.admitted_by = request.user
            admission.save()
            # Lock the bed atomically so it can't be assigned to two patients
            if admission.bed:
                Bed.objects.filter(pk=admission.bed.pk).update(is_occupied=True)
        messages.success(request, f'{admission.patient.full_name} admitted successfully.')
        return redirect('wards:admission_list')
    return render(request, 'wards/admission_form.html', {'form': form})


@login_required
@role_required('ADMIN', 'RECEPTIONIST', 'DOCTOR')
def admission_discharge(request, pk):
    admission = get_object_or_404(Admission, pk=pk, status='ADMITTED')
    form = DischargeForm(request.POST or None, instance=admission)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            admission.status = Admission.Status.DISCHARGED
            admission.discharge_date = timezone.now()
            admission.save()
            if admission.bed:
                Bed.objects.filter(pk=admission.bed.pk).update(is_occupied=False)
        messages.success(request, f'{admission.patient.full_name} discharged.')
        return redirect('wards:admission_list')
    return render(request, 'wards/discharge_form.html', {'form': form, 'admission': admission})


@login_required
def ward_status(request):
    wards = Ward.objects.prefetch_related('beds').all()
    return render(request, 'wards/ward_status.html', {'wards': wards})
