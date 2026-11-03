from django.contrib import admin
from django.shortcuts import render

from . import ratelimit


def admin_login(request, **kwargs):
    """
    The admin sign-in page, closed for a while after repeated wrong
    passwords from one IP address, so passwords cannot be guessed at speed.
    """
    if request.method == "POST" and ratelimit.is_limited(
        "admin_login", request, ratelimit.ADMIN_LOGIN_FAILURE_LIMIT
    ):
        return render(request, "core/login_locked.html", status=429)
    return admin.site.login(request, **kwargs)
