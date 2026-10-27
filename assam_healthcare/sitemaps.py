"""
Sitemap of public pages. Only published, active content is listed; admin,
form-success pages and private documents are never included.
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.careers.views import open_jobs
from apps.catalog.models import Product
from apps.content.models import Page


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"

    def items(self):
        return [
            "home",
            "about",
            "product_list",
            "partners",
            "team",
            "job_list",
            "contact",
            "create_inquiry",
        ]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    changefreq = "weekly"

    def items(self):
        return Product.objects.public().order_by("pk")

    def lastmod(self, obj):
        return obj.updated_at


class JobSitemap(Sitemap):
    changefreq = "weekly"

    def items(self):
        return open_jobs()

    def lastmod(self, obj):
        return obj.updated_at


class PageSitemap(Sitemap):
    def items(self):
        # The "about" page is already listed as a static view.
        return Page.objects.filter(is_published=True).exclude(slug="about")

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    "static": StaticViewSitemap,
    "products": ProductSitemap,
    "jobs": JobSitemap,
    "pages": PageSitemap,
}
