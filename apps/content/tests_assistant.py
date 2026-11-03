from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.core.testing import make_category, make_company, make_product, make_variant
from apps.content.models import AssistantAnswer, SiteSettings


class AssistantWidgetTests(TestCase):
    def test_widget_is_on_public_pages_and_hidden_until_script_runs(self):
        for url in (reverse("home"), reverse("product_list"), reverse("contact")):
            with self.subTest(url=url):
                html = self.client.get(url).content.decode()
                self.assertIn("data-assistant\n", html)
                self.assertIn("js/assistant.js", html)

        root = self.client.get(reverse("home")).content.decode()
        root = root[root.index("data-assistant\n"):]
        self.assertIn("hidden>", root[: root.index(">") + 1])

    def test_only_published_answers_are_offered(self):
        AssistantAnswer.objects.create(
            question="Do you deliver outside Multan?",
            answer="Yes, across our territories.",
        )
        AssistantAnswer.objects.create(
            question="Draft question", answer="Not ready", is_published=False
        )

        response = self.client.get(reverse("home"))

        self.assertContains(response, "Do you deliver outside Multan?")
        self.assertContains(response, "Yes, across our territories.")
        self.assertNotContains(response, "Draft question")

    def test_answer_text_is_escaped_and_keeps_paragraphs(self):
        AssistantAnswer.objects.create(
            question="Payment terms?",
            answer="<script>alert(1)</script>\n\nSecond paragraph",
            link_label="See products",
            link_url="/products/",
        )

        response = self.client.get(reverse("home"))

        self.assertNotContains(response, "<script>alert(1)</script>")
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertContains(response, "<p>Second paragraph</p>")
        self.assertContains(response, 'href="/products/" class="btn btn-sm btn-secondary mt-3">See products')

    def test_whatsapp_option_uses_site_settings(self):
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "Chat on WhatsApp")
        self.assertContains(response, "Call our sales team on 0300-9631291")

        SiteSettings.objects.create(company_name="Assam Healthcare", whatsapp="0300-1112223")
        response = self.client.get(reverse("home"))

        self.assertContains(response, 'data-whatsapp-url="https://wa.me/923001112223"')
        self.assertContains(response, "https://wa.me/923001112223?text=Hello%20Assam%20Healthcare")


class AssistantAnswerValidationTests(TestCase):
    def test_links_must_stay_on_site_or_use_https(self):
        for url in ("javascript:alert(1)", "//evil.example", "http://example.com", "products/"):
            with self.subTest(url=url):
                answer = AssistantAnswer(question="Q", answer="A", link_label="Go", link_url=url)
                with self.assertRaises(ValidationError):
                    answer.full_clean()

        for url in ("/products/", "https://wa.me/923009631291"):
            with self.subTest(url=url):
                AssistantAnswer(question="Q", answer="A", link_label="Go", link_url=url).full_clean()

    def test_link_label_and_page_go_together(self):
        with self.assertRaises(ValidationError):
            AssistantAnswer(question="Q", answer="A", link_label="Go").full_clean()
        with self.assertRaises(ValidationError):
            AssistantAnswer(question="Q", answer="A", link_url="/team/").full_clean()


class AssistantProductSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        company = make_company("Bain Medical")
        category = make_category("Dialysis")
        cls.dialyzer = make_product("Hollow Fiber Dialyzer", category, company)
        make_variant(cls.dialyzer, "16-PF")
        make_product("Hidden Dialyzer", category, company, is_active=False)
        hidden_company = make_company("Old Supplier", is_active=False)
        make_product("Old Supplier Dialyzer", category, hidden_company)
        cls.url = reverse("assistant_product_search")

    def search(self, query):
        response = self.client.get(self.url, {"q": query})
        self.assertEqual(response.status_code, 200)
        return response.json()["results"]

    def test_finds_public_products_by_name_variant_and_company(self):
        for query in ("dialyzer", "16-PF", "bain"):
            with self.subTest(query=query):
                names = [result["name"] for result in self.search(query)]
                self.assertEqual(names, ["Hollow Fiber Dialyzer"])

    def test_returns_only_public_fields(self):
        (result,) = self.search("dialyzer")
        self.assertEqual(
            result,
            {
                "name": "Hollow Fiber Dialyzer",
                "company": "Bain Medical",
                "category": "Dialysis",
                "url": self.dialyzer.get_absolute_url(),
                "quote_url": f"{reverse('create_inquiry')}?product={self.dialyzer.pk}",
            },
        )

    def test_short_or_missing_queries_return_nothing(self):
        self.assertEqual(self.search(""), [])
        self.assertEqual(self.search("d"), [])

    def test_results_are_capped(self):
        category = make_category("Bulk")
        company = make_company("Bulk Co")
        for index in range(10):
            make_product(f"Gauze roll {index}", category, company)

        self.assertEqual(len(self.search("gauze")), 6)

    def test_only_get_is_allowed_and_not_indexed(self):
        self.assertEqual(self.client.post(self.url).status_code, 405)
        self.assertEqual(self.client.get(self.url)["X-Robots-Tag"], "noindex")
        self.assertContains(self.client.get("/robots.txt"), "Disallow: /assistant/")
