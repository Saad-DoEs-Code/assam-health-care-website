from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.content.context_processors import phone_to_international, site_settings
from apps.content.models import Page, SiteSettings


class PhoneFormattingTests(TestCase):
    def test_phone_to_international(self):
        cases = {
            "0300-9631291": "+923009631291",
            "+92 300 9631291": "+923009631291",
            "0092 300 9631291": "+923009631291",
            "": "",
            "n/a": "",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(phone_to_international(value), expected)


class SiteSettingsContextTests(TestCase):
    def get_context(self):
        return site_settings(RequestFactory().get("/"))

    def test_defaults_when_no_settings_exist(self):
        contact = self.get_context()["company_contact"]

        self.assertEqual(contact["name"], "Assam Healthcare (Pvt.) Ltd.")
        self.assertEqual(contact["tagline"], "Quality. Trust. Service.")
        self.assertEqual(contact["phone"], "0300-9631291")
        self.assertEqual(contact["phone_href"], "tel:+923009631291")
        self.assertIn("Nishter Road, Multan", contact["address"])
        # Never invented.
        self.assertEqual(contact["email"], "")
        self.assertEqual(contact["whatsapp_href"], "")

    def test_values_come_from_site_settings(self):
        SiteSettings.objects.create(
            company_name="Assam Healthcare (Pvt.) Ltd.",
            phone="+92 300 9631291",
            email="info@example.com",
            whatsapp="0300-1112223",
        )
        contact = self.get_context()["company_contact"]

        self.assertEqual(contact["phone_href"], "tel:+923009631291")
        self.assertEqual(contact["email"], "info@example.com")
        self.assertEqual(contact["whatsapp_href"], "https://wa.me/923001112223")

    def test_pages_render_without_site_settings(self):
        for name in ["home", "about", "contact", "product_list", "partners", "team", "job_list", "create_inquiry"]:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'href="tel:+923009631291"')


class CmsPageTests(TestCase):
    def test_published_page_is_shown(self):
        Page.objects.create(title="Privacy Policy", slug="privacy", content="We respect <privacy>.")
        response = self.client.get(reverse("page_detail", args=["privacy"]))
        self.assertContains(response, "Privacy Policy")
        self.assertContains(response, "We respect &lt;privacy&gt;.")

    def test_unpublished_page_returns_404(self):
        Page.objects.create(title="Draft", slug="draft", is_published=False)
        response = self.client.get(reverse("page_detail", args=["draft"]))
        self.assertEqual(response.status_code, 404)

    def test_about_page_uses_cms_content_when_published(self):
        Page.objects.create(title="Our Story", slug="about", content="Founded in Multan.")
        response = self.client.get(reverse("about"))
        self.assertContains(response, "Our Story")
        self.assertContains(response, "Founded in Multan.")

    def test_about_page_falls_back_when_unpublished(self):
        Page.objects.create(title="Secret Draft", slug="about", content="Draft text", is_published=False)
        response = self.client.get(reverse("about"))
        self.assertNotContains(response, "Draft text")
        self.assertContains(response, "headquartered in Multan")


class ContactPageTests(TestCase):
    def test_contact_page_shows_confirmed_details(self):
        response = self.client.get(reverse("contact"))
        self.assertContains(response, "Street #3, Al-Raheem Colony, Nishter Road, Multan, Pakistan.")
        self.assertContains(response, "0300-9631291")
        self.assertContains(response, "Quality. Trust. Service.")
        self.assertNotContains(response, "mailto:")
