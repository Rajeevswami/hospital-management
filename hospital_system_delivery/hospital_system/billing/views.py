from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.http import HttpResponse
from core.decorators import role_required
from .models import Invoice, InvoiceItem, Payment
from .forms import PatientSelectForm, PaymentForm
from .pdf_utils import generate_invoice_pdf
from patients.models import Patient
from appointments.models import Appointment
from wards.models import Admission
from pharmacy.models import Prescription


@login_required
def invoice_list(request):
    invoices = Invoice.objects.select_related('patient').prefetch_related('items', 'payments')
    return render(request, 'billing/invoice_list.html', {'invoices': invoices})


@login_required
@role_required('ADMIN', 'RECEPTIONIST')
def invoice_create_select_patient(request):
    """Step 1: pick the patient to bill."""
    form = PatientSelectForm(request.GET or None)
    if form.is_valid():
        return redirect('billing:invoice_create', patient_id=form.cleaned_data['patient'].pk)
    return render(request, 'billing/select_patient.html', {'form': form})


@login_required
@role_required('ADMIN', 'RECEPTIONIST')
def invoice_create(request, patient_id):
    """Step 2: show unbilled charges for this patient, let staff pick which to invoice."""
    patient = get_object_or_404(Patient, pk=patient_id)

    unbilled_appointments = Appointment.objects.filter(
        patient=patient, is_billed=False, status=Appointment.Status.COMPLETED
    )
    unbilled_admissions = Admission.objects.filter(
        patient=patient, is_billed=False, status=Admission.Status.DISCHARGED
    )
    unbilled_prescriptions = Prescription.objects.filter(patient=patient, is_billed=False).prefetch_related('items')

    if request.method == 'POST':
        selected_appts = request.POST.getlist('appointments')
        selected_admissions = request.POST.getlist('admissions')
        selected_prescriptions = request.POST.getlist('prescriptions')

        if not (selected_appts or selected_admissions or selected_prescriptions):
            messages.error(request, 'Select at least one charge to invoice.')
        else:
            with transaction.atomic():
                invoice = Invoice.objects.create(patient=patient, created_by=request.user)

                for appt in Appointment.objects.filter(pk__in=selected_appts, is_billed=False):
                    InvoiceItem.objects.create(
                        invoice=invoice, item_type=InvoiceItem.ItemType.CONSULTATION,
                        description=f"Consultation - {appt.doctor} on {appt.appointment_date}",
                        amount=appt.fee or 0,
                    )
                    appt.is_billed = True
                    appt.save(update_fields=['is_billed'])

                for adm in Admission.objects.filter(pk__in=selected_admissions, is_billed=False):
                    rate = adm.bed.ward.charge_per_day if adm.bed else 0
                    days = adm.days_admitted
                    InvoiceItem.objects.create(
                        invoice=invoice, item_type=InvoiceItem.ItemType.ADMISSION,
                        description=f"Admission - {adm.diagnosis} ({days} days @ ₹{rate}/day, {adm.bed})",
                        amount=rate * days,
                    )
                    adm.is_billed = True
                    adm.save(update_fields=['is_billed'])

                for pres in Prescription.objects.filter(pk__in=selected_prescriptions, is_billed=False):
                    InvoiceItem.objects.create(
                        invoice=invoice, item_type=InvoiceItem.ItemType.MEDICINE,
                        description=f"Medicines - Prescription #{pres.pk}",
                        amount=pres.total_cost,
                    )
                    pres.is_billed = True
                    pres.save(update_fields=['is_billed'])

                invoice.refresh_status()

            messages.success(request, f'Invoice {invoice.invoice_number} created.')
            return redirect('billing:invoice_detail', pk=invoice.pk)

    return render(request, 'billing/invoice_create.html', {
        'patient': patient,
        'unbilled_appointments': unbilled_appointments,
        'unbilled_admissions': unbilled_admissions,
        'unbilled_prescriptions': unbilled_prescriptions,
    })


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    payment_form = PaymentForm(invoice=invoice)
    return render(request, 'billing/invoice_detail.html', {'invoice': invoice, 'payment_form': payment_form})


@login_required
@role_required('ADMIN', 'RECEPTIONIST')
def record_payment(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if invoice.status == Invoice.Status.PAID:
        messages.info(request, 'This invoice is already fully paid.')
        return redirect('billing:invoice_detail', pk=invoice.pk)

    form = PaymentForm(request.POST or None, invoice=invoice)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.received_by = request.user
            payment.save()
            invoice.refresh_status()
        messages.success(request, f'Payment of ₹{payment.amount} recorded ({payment.transaction_id}).')
    else:
        for error in form.errors.get('amount', []):
            messages.error(request, error)
    return redirect('billing:invoice_detail', pk=invoice.pk)


@login_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    buffer = generate_invoice_pdf(invoice)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
    return response
