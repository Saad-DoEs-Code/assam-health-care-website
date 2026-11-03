"""
URL configuration for assam_healthcare project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import path, include, reverse
from django.views.decorators.http import require_GET

from apps.core.views import admin_login

from .sitemaps import sitemaps


@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        # The admin address is left out on purpose: listing it here would
        # tell bots where to try passwords. Admin pages are noindex anyway.
        "Disallow: /inquiry/success/",
        "Disallow: /assistant/",
        "Disallow: /careers/application-received/",
        f"Sitemap: {request.build_absolute_uri(reverse('sitemap'))}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


admin.site.site_header = "Assam Healthcare administration"
admin.site.site_title = "Assam Healthcare admin"
admin.site.index_title = "Website management"

urlpatterns = [
    # Must come before admin.site.urls so it replaces the stock login view.
    path(f"{settings.ADMIN_URL}login/", admin_login, name="admin_login"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("robots.txt", robots_txt, name="robots_txt"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="sitemap",
    ),
    path("", include("apps.home.urls")),
    path("", include("apps.content.urls")),
    path("", include("apps.inquiries.urls")),
    path("", include("apps.catalog.urls")),
    path("", include("apps.companies.urls")),
    path("", include("apps.team.urls")),
    path("", include("apps.careers.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
