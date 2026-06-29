from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from . import audit_context
from .models import AuditLog

from patients.models import Patient
from wards.models import Admission
from pharmacy.models import Prescription
from billing.models import Invoice, Payment

AUDITED_MODELS = [Patient, Admission, Prescription, Invoice, Payment]


def _log(action, instance):
    AuditLog.objects.create(
        user=audit_context.get_current_user(),
        action=action,
        model_name=instance.__class__.__name__,
        object_id=str(instance.pk),
        object_repr=str(instance)[:255],
        ip_address=audit_context.get_current_ip(),
    )


def _make_save_handler():
    def handler(sender, instance, created, **kwargs):
        _log(AuditLog.Action.CREATE if created else AuditLog.Action.UPDATE, instance)
    return handler


def _make_delete_handler():
    def handler(sender, instance, **kwargs):
        _log(AuditLog.Action.DELETE, instance)
    return handler


def connect_audit_signals():
    for model in AUDITED_MODELS:
        post_save.connect(_make_save_handler(), sender=model, weak=False)
        post_delete.connect(_make_delete_handler(), sender=model, weak=False)
