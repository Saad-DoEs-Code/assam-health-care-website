import re

from django.test import TestCase
from django.urls import reverse

from apps.content.models import Page
from apps.core.testing import make_category, make_company, make_product


class HomePageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.bain = make_company("Bain Medical", is_official_partner=True)
        cls.supplier = make_company("Generic Supplier")
        make_company("Retired Partner", is_official_partner=True, is_active=False)

        cls.dialysis = make_category("Dialysis")
        cls.empty_category = make_category("Empty Category")
        hidden_category = make_category("Hidden Category", is_active=False)

        cls.featured = make_product("Hollow Fiber Dialyzer", cls.dialysis, cls.bain, is_featured=True)
        make_product("Hidden Featured", hidden_category, cls.bain, is_featured=True)
        make_product(
            "Inactive Supplier Featured", cls.dialysis,
            make_company("Gone Co", is_active=False), is_featured=True,
        )

    def test_partners_come_from_database(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Bain Medical")
        self.assertNotContains(response, "Retired Partner")
        # Non-partners are never presented as official partners.
        partners = list(response.context["partners"])
        self.assertEqual(partners, [self.bain])

    def test_featured_products_respect_visibility_rules(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Hollow Fiber Dialyzer")
        self.assertNotContains(response, "Hidden Featured")
        self.assertNotContains(response, "Inactive Supplier Featured")
        self.assertContains(response, self.featured.get_absolute_url())

    def test_categories_link_to_filtered_catalogue(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, self.dialysis.get_absolute_url())
        # Categories without public products are omitted.
        self.assertNotContains(response, "Empty Category")
        self.assertNotContains(response, "Hidden Category")

    def test_empty_database_renders(self):
        from apps.catalog.models import Product
        from apps.companies.models import Company

        Product.objects.all().delete()
        Company.objects.all().delete()
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Request a Quote")


class SiteWideTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        company = make_company("Bain Medical")
        category = make_category("Dialysis")
        cls.product = make_product("Hollow Fiber Dialyzer", category, company)
        cls.hidden = make_product("Secret Product", category, company, is_active=False)
        Page.objects.create(title="Privacy", slug="privacy")
        Page.objects.create(title="Draft", slug="draft", is_published=False)

    def test_navigation_links_resolve(self):
        response = self.client.get(reverse("home"))
        html = response.content.decode()
        nav = html[html.index('id="primary-navigation"'):html.index("</nav>")]
        hrefs = re.findall(r'href="([^"]+)"', nav)

        self.assertGreaterEqual(len(hrefs), 7)
        for href in hrefs:
            with self.subTest(href=href):
                self.assertEqual(self.client.get(href).status_code, 200)

    def test_no_placeholder_links(self):
        for name in ["home", "about", "contact", "product_list", "partners", "team", "job_list"]:
            with self.subTest(page=name):
                html = self.client.get(reverse(name)).content.decode()
                self.assertNotIn('href="#"', html)
                self.assertNotIn('href="/#', html)

    def test_sitemap_lists_only_public_content(self):
        response = self.client.get(reverse("sitemap"))
        self.assertContains(response, self.product.get_absolute_url())
        self.assertContains(response, "/pages/privacy/")
        self.assertNotContains(response, "secret-product")
        self.assertNotContains(response, "/pages/draft/")
        self.assertNotContains(response, "/admin/")

    def test_robots_txt(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertContains(response, "Disallow: /admin/")
        self.assertContains(response, "Sitemap: http://testserver/sitemap.xml")

    def test_pages_have_title_description_and_canonical(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertContains(response, "<title>Hollow Fiber Dialyzer | Bain Medical")
        self.assertContains(response, '<meta name="description"')
        self.assertContains(response, f'<link rel="canonical" href="http://testserver{self.product.get_absolute_url()}">')

    def test_custom_404_page(self):
        response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Page not found", status_code=404)
