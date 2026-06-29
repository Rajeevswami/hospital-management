from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from .signals import connect_audit_signals
        connect_audit_signals()
