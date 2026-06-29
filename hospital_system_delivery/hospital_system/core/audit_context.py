"""
Thread-local storage to make the current request's user/IP available inside
Django signal handlers (which don't receive the request object directly).
Set by core.middleware.AuditContextMiddleware on every request.
"""
import threading

_local = threading.local()


def set_current_request(user, ip_address):
    _local.user = user
    _local.ip_address = ip_address


def get_current_user():
    return getattr(_local, 'user', None)


def get_current_ip():
    return getattr(_local, 'ip_address', None)
