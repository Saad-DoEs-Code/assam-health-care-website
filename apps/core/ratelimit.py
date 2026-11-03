"""
Per-visitor limits on how often public forms can be submitted.

Counts live in Django's cache (a shared file cache in production, see
CACHES in settings), keyed by the visitor's IP address. A limit is a number
of attempts per time window, for example 10 quotation requests an hour.
"""

from django.conf import settings
from django.core.cache import cache

# Form submissions allowed per IP address: (attempts, window in seconds).
INQUIRY_LIMIT = (10, 60 * 60)
JOB_APPLICATION_LIMIT = (5, 60 * 60)
ADMIN_LOGIN_FAILURE_LIMIT = (10, 15 * 60)


def client_ip(request):
    """
    The visitor's IP address.

    Behind nginx, Django only sees the proxy's socket, so the address comes
    from the X-Real-IP header that nginx sets (and overwrites if a visitor
    sends their own). It is trusted only when DJANGO_BEHIND_PROXY is on.
    """
    if getattr(settings, "SECURE_PROXY_SSL_HEADER", None):
        real_ip = request.META.get("HTTP_X_REAL_IP", "").strip()
        if real_ip:
            return real_ip
    return request.META.get("REMOTE_ADDR", "") or "unknown"


def _cache_key(scope, request):
    return f"ratelimit:{scope}:{client_ip(request)}"


def count_attempt(scope, request, limit):
    """Record one attempt and return how many were made in the window."""
    _attempts, window = limit
    key = _cache_key(scope, request)
    # add() only sets the key when it is missing, so the window starts at
    # the first attempt and is not extended by later ones.
    cache.add(key, 0, timeout=window)
    try:
        return cache.incr(key)
    except ValueError:
        # The key expired between add() and incr().
        cache.set(key, 1, timeout=window)
        return 1


def is_limited(scope, request, limit):
    """True when the visitor has already used up their attempts."""
    attempts, _window = limit
    return cache.get(_cache_key(scope, request), 0) >= attempts


def record_login_failure(sender, credentials=None, request=None, **kwargs):
    """Signal receiver: count a failed admin sign-in against the visitor's IP."""
    if request is not None:
        count_attempt("admin_login", request, ADMIN_LOGIN_FAILURE_LIMIT)
