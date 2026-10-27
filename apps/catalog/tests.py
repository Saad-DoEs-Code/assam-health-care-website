from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.catalog.models import ProductDocument
from apps.catalog.views import PRODUCTS_PER_PAGE
from apps.core.testing import make_category, make_company, make_product, make_variant

import shutil
import tempfile

TEMP_MEDIA_ROOT = tempfile.mkdtemp()


class CatalogueListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.bain = make_company("Bain Medical")
        cls.marflow = make_company("Marflow")
        cls.dialysis = make_category("Dialysis")
        cls.urology = make_category("Urology")

        cls.dialyzer = make_product(
            "Hollow Fiber Dialyzer", cls.dialysis, cls.bain,
            short_description="High-flux dialyzer",
        )
        cls.catheter = make_product("Foley Catheter", cls.urology, cls.marflow)
        cls.bloodline = make_product(
            "Blood Line Set", cls.dialysis, cls.marflow,
            description="Arterial and venous lines",
        )

        cls.inactive = make_product(
            "Inactive Product", cls.dialysis, cls.bain, is_active=False
        )
        hidden_category = make_category("Hidden", is_active=False)
        cls.in_hidden_category = make_product(
            "Hidden Category Product", hidden_category, cls.bain
        )
        hidden_company = make_company("Hidden Co", is_active=False)
        cls.from_hidden_company = make_product(
            "Hidden Company Product", cls.dialysis, hidden_company
        )
        cls.url = reverse("product_list")

    def listed_names(self, response):
        return [product.name for product in response.context["page_obj"]]

    def test_active_products_appear(self):
        response = self.client.get(self.url)
        self.assertEqual(
            sorted(self.listed_names(response)),
            ["Blood Line Set", "Foley Catheter", "Hollow Fiber Dialyzer"],
        )

    def test_hidden_products_never_appear(self):
        response = self.client.get(self.url)
        for name in ["Inactive Product", "Hidden Category Product", "Hidden Company Product"]:
            self.assertNotContains(response, name)

    def test_search_is_case_insensitive_and_covers_fields(self):
        cases = {
            "DIALYZER": ["Hollow Fiber Dialyzer"],
            "high-flux": ["Hollow Fiber Dialyzer"],
            "venous": ["Blood Line Set"],
            "marflow": ["Blood Line Set", "Foley Catheter"],
        }
        for query, expected in cases.items():
            with self.subTest(query=query):
                response = self.client.get(self.url, {"q": query})
                self.assertEqual(sorted(self.listed_names(response)), expected)

    def test_search_matches_variant_names_without_duplicates(self):
        make_variant(self.dialyzer, "14-PF")
        make_variant(self.dialyzer, "16-PF")
        response = self.client.get(self.url, {"q": "PF"})
        self.assertEqual(self.listed_names(response), ["Hollow Fiber Dialyzer"])

    def test_search_cannot_reveal_hidden_products(self):
        response = self.client.get(self.url, {"q": "Hidden"})
        self.assertEqual(self.listed_names(response), [])
        self.assertContains(response, "No matching products")

    def test_category_filter(self):
        response = self.client.get(self.url, {"category": "urology"})
        self.assertEqual(self.listed_names(response), ["Foley Catheter"])

    def test_search_and_category_combined(self):
        response = self.client.get(self.url, {"category": "dialysis", "q": "marflow"})
        self.assertEqual(self.listed_names(response), ["Blood Line Set"])

    def test_inactive_or_unknown_category_shows_nothing(self):
        for slug in ["hidden", "does-not-exist"]:
            with self.subTest(slug=slug):
                response = self.client.get(self.url, {"category": slug})
                self.assertEqual(self.listed_names(response), [])

    def test_subcategory_products_appear_under_parent(self):
        sub = make_category("Dialysis Needles", parent=self.dialysis)
        make_product("AV Fistula Needle", sub, self.bain)
        response = self.client.get(self.url, {"category": "dialysis"})
        self.assertIn("AV Fistula Needle", self.listed_names(response))

    def test_company_filter(self):
        response = self.client.get(self.url, {"company": "bain-medical"})
        self.assertEqual(self.listed_names(response), ["Hollow Fiber Dialyzer"])

    def test_pagination_preserves_filters(self):
        for n in range(PRODUCTS_PER_PAGE + 2):
            make_product(f"Dialysis Item {n:02d}", self.dialysis, self.bain)

        response = self.client.get(self.url, {"category": "dialysis", "q": "item"})
        self.assertEqual(len(response.context["page_obj"]), PRODUCTS_PER_PAGE)
        self.assertContains(response, "category=dialysis&amp;q=item&amp;page=2")

        page_two = self.client.get(self.url, {"category": "dialysis", "q": "item", "page": 2})
        self.assertEqual(len(page_two.context["page_obj"]), 2)

    def test_invalid_page_number_falls_back(self):
        response = self.client.get(self.url, {"page": "abc"})
        self.assertEqual(response.status_code, 200)

    def test_products_without_images_render_placeholder(self):
        response = self.client.get(self.url)
        self.assertContains(response, "card__image--placeholder")

    def test_list_uses_constant_number_of_queries(self):
        for n in range(8):
            make_product(f"Extra {n}", self.dialysis, self.bain)
        # Settings, count, products, images, categories (+ session-free).
        with self.assertNumQueries(5):
            self.client.get(self.url)

    def test_quote_links_present(self):
        response = self.client.get(self.url)
        self.assertContains(response, f"{reverse('create_inquiry')}?product={self.dialyzer.pk}")


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ProductDetailTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company("Bain Medical", is_official_partner=True)
        cls.category = make_category("Dialysis")
        cls.product = make_product(
            "Hollow Fiber Dialyzer", cls.category, cls.company,
            description="Line one\n\nLine <b>two</b>",
        )
        make_variant(cls.product, "14-PF", description="1.4 m2")
        make_variant(cls.product, "Old Size", is_active=False)

        ProductDocument.objects.create(
            product=cls.product, title="Public Brochure",
            file=SimpleUploadedFile("brochure.pdf", b"%PDF-1.4"), is_public=True,
        )
        ProductDocument.objects.create(
            product=cls.product, title="Internal Price Sheet",
            file=SimpleUploadedFile("internal.pdf", b"%PDF-1.4"), is_public=False,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_detail_page_shows_product_information(self):
        response = self.client.get(self.product.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1>Hollow Fiber Dialyzer</h1>", html=True)
        self.assertContains(response, "Bain Medical")
        self.assertContains(response, "Official distribution partner")
        self.assertContains(response, "14-PF")
        self.assertNotContains(response, "Old Size")
        self.assertContains(response, "Product image not yet available")
        self.assertContains(response, f"?product={self.product.pk}")
        self.assertContains(response, 'aria-label="Breadcrumb"')

    def test_description_is_escaped(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertContains(response, "Line &lt;b&gt;two&lt;/b&gt;")

    def test_only_public_documents_are_listed(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertContains(response, "Public Brochure")
        self.assertNotContains(response, "Internal Price Sheet")
        self.assertNotContains(response, "internal")

    def test_unknown_slug_returns_404(self):
        response = self.client.get(reverse("product_detail", args=["no-such-product"]))
        self.assertEqual(response.status_code, 404)

    def test_hidden_products_return_404(self):
        cases = [
            make_product("Inactive", self.category, self.company, is_active=False),
            make_product("In Hidden Cat", make_category("Hidden", is_active=False), self.company),
            make_product("Hidden Co Product", self.category, make_company("Gone", is_active=False)),
        ]
        for product in cases:
            with self.subTest(product=product.name):
                response = self.client.get(product.get_absolute_url())
                self.assertEqual(response.status_code, 404)
