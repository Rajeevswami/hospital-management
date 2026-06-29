from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from core.decorators import role_required
from .models import Appointment
from .forms import AppointmentForm


@login_required
def appointment_list(request):
    appointments = Appointment.objects.select_related('patient', 'doctor__user')
    # Doctors only see their own appointments - everyone else (admin/receptionist) sees all
    if request.user.is_doctor:
        appointments = appointments.filter(doctor__user=request.user)
    status_filter = request.GET.get('status')
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    return render(request, 'appointments/appointment_list.html', {
        'appointments': appointments, 'status_filter': status_filter,
    })


@login_required
@role_required('ADMIN', 'RECEPTIONIST')
def appointment_create(request):
    form = AppointmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        appt = form.save(commit=False)
        appt.created_by = request.user
        appt.save()
        messages.success(request, 'Appointment booked successfully.')
        return redirect('appointments:list')
    return render(request, 'appointments/appointment_form.html', {'form': form})


@login_required
def appointment_update_status(request, pk, new_status):
    appointment = get_object_or_404(Appointment, pk=pk)
    if new_status not in dict(Appointment.Status.choices):
        messages.error(request, 'Invalid status.')
        return redirect('appointments:list')
    # Doctor can only mark their own appointments; admin/receptionist can mark any
    if request.user.is_doctor and appointment.doctor.user != request.user:
        messages.error(request, "You can't modify another doctor's appointment.")
        return redirect('appointments:list')
    appointment.status = new_status
    appointment.save()
    messages.success(request, f'Appointment marked as {appointment.get_status_display()}.')
    return redirect('appointments:list')
