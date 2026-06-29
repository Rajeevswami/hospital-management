from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from core.decorators import role_required
from .models import Doctor
from .forms import DoctorUserForm, DoctorProfileForm


@login_required
def doctor_list(request):
    doctors = Doctor.objects.select_related('user').filter(is_active=True)
    return render(request, 'doctors/doctor_list.html', {'doctors': doctors})


@login_required
def doctor_detail(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    return render(request, 'doctors/doctor_detail.html', {'doctor': doctor})


@login_required
@role_required('ADMIN')
def doctor_create(request):
    user_form = DoctorUserForm(request.POST or None)
    profile_form = DoctorProfileForm(request.POST or None)

    if request.method == 'POST' and user_form.is_valid() and profile_form.is_valid():
        with transaction.atomic():
            user = user_form.save()
            doctor = profile_form.save(commit=False)
            doctor.user = user
            doctor.save()
        messages.success(request, f'Dr. {user.get_full_name()} added successfully.')
        return redirect('doctors:list')

    return render(request, 'doctors/doctor_form.html', {
        'user_form': user_form, 'profile_form': profile_form,
    })
