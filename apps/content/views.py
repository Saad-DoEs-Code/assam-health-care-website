from django.shortcuts import get_object_or_404, render

from apps.companies.models import Company

from .models import Page

# CMS pages with these slugs replace the built-in text on the matching page.
ABOUT_PAGE_SLUG = "about"


def about(request):
    context = {
        "page": Page.objects.filter(slug=ABOUT_PAGE_SLUG, is_published=True).first(),
        "partners": Company.objects.filter(is_official_partner=True, is_active=True),
    }
    return render(request, "content/about.html", context)


def contact(request):
    return render(request, "content/contact.html")


def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, "content/page_detail.html", {"page": page})
