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


class StaticAssetTests(TestCase):
    def test_every_static_reference_in_templates_exists(self):
        import re
        from pathlib import Path

        from django.conf import settings

        static_root = Path(settings.BASE_DIR) / "static"
        missing = []
        for template in (Path(settings.BASE_DIR) / "templates").rglob("*.html"):
            for path in re.findall(r"{% static '([^']+)' %}", template.read_text(encoding="utf-8")):
                if not (static_root / path).exists():
                    missing.append(f"{template.name}: {path}")
        self.assertEqual(missing, [])

    def test_compiled_stylesheet_and_fonts_exist(self):
        from pathlib import Path

        from django.conf import settings

        static_root = Path(settings.BASE_DIR) / "static"
        for path in [
            "css/site.css",
            "fonts/manrope-latin-wght-normal.woff2",
            "fonts/source-serif-4-latin-wght-normal.woff2",
        ]:
            with self.subTest(path=path):
                self.assertTrue((static_root / path).exists())


class CategoryArtTests(TestCase):
    def test_artwork_exists_for_known_category_slugs(self):
        from pathlib import Path

        from django.conf import settings

        art_dir = Path(settings.BASE_DIR) / "static" / "images" / "categories"
        for slug in [
            "dialysis",
            "urology",
            "interventional-cardiology",
            "anesthesia-respiratory-care",
            "gastroenterology-hepatobiliary",
            "neurosurgery",
            "interventional-radiology-biopsy",
            "general-surgery",
            "diagnostics-equipment",
            "hygiene-disinfection",
            "default",
        ]:
            with self.subTest(slug=slug):
                self.assertTrue((art_dir / f"{slug}.svg").exists())

    def test_lookup_uses_own_then_parent_then_default(self):
        from apps.catalog.models import Category
        from apps.content.templatetags.site_tags import category_art

        dialysis = Category(name="Dialysis", slug="dialysis")
        child = Category(name="Dialysis Needles", slug="dialysis-needles", parent=dialysis)
        unknown = Category(name="New Range", slug="new-range")

        self.assertTrue(category_art(dialysis).endswith("/images/categories/dialysis.svg"))
        self.assertTrue(category_art(child).endswith("/images/categories/dialysis.svg"))
        self.assertTrue(category_art(unknown).endswith("/images/categories/default.svg"))


class LeadershipMessageTests(TestCase):
    def make_message(self, **kwargs):
        from apps.content.models import LeadershipMessage

        defaults = {
            "name": "Test Leader",
            "designation": "Chief Executive Officer",
            "message": "First paragraph of the message.\n\nSecond <b>paragraph</b>.",
            "is_published": True,
        }
        defaults.update(kwargs)
        return LeadershipMessage.objects.create(**defaults)

    def test_hidden_when_no_message_exists(self):
        for name in ["home", "about"]:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertNotContains(response, "Leadership message")
                self.assertIsNone(response.context["leadership_message"])

    def test_hidden_while_unpublished(self):
        self.make_message(is_published=False)
        for name in ["home", "about"]:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertNotContains(response, "Test Leader")

    def test_homepage_shows_excerpt_and_link(self):
        self.make_message(excerpt="Our short quote for the homepage.")
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Our short quote for the homepage.")
        self.assertContains(response, "Test Leader")
        self.assertContains(response, "Chief Executive Officer")
        self.assertContains(response, f"{reverse('about')}#leadership-message")
        self.assertNotContains(response, "Second &lt;b&gt;paragraph")

    def test_homepage_falls_back_to_start_of_message(self):
        self.make_message(excerpt="")
        response = self.client.get(reverse("home"))
        self.assertContains(response, "First paragraph of the message.")

    def test_about_page_shows_full_message_escaped(self):
        self.make_message()
        response = self.client.get(reverse("about"))
        self.assertContains(response, 'id="leadership-message"')
        self.assertContains(response, "A message from Test Leader")
        self.assertContains(response, "<p>First paragraph of the message.</p>", html=True)
        self.assertContains(response, "Second &lt;b&gt;paragraph&lt;/b&gt;.")

    def test_missing_photo_uses_placeholder(self):
        self.make_message()
        response = self.client.get(reverse("about"))
        self.assertContains(response, "data-leadership-photo-placeholder")

    def test_most_recently_updated_published_message_is_shown(self):
        from apps.content.models import LeadershipMessage

        older = self.make_message(name="Older Message")
        self.make_message(name="Newer Message")
        older.save()  # updating it makes it the most recent

        self.assertEqual(LeadershipMessage.get_published(), older)

    def test_photo_validation(self):
        from django.core.exceptions import ValidationError
        from django.core.files.uploadedfile import SimpleUploadedFile

        message = self.make_message()
        message.photo = SimpleUploadedFile("portrait.gif", b"GIF89a")
        with self.assertRaises(ValidationError):
            message.full_clean()

    def test_admin_lists_messages(self):
        from django.contrib.auth import get_user_model

        self.make_message()
        user = get_user_model().objects.create_superuser("staff", "staff@example.com", "test-password-123")
        self.client.force_login(user)
        response = self.client.get(reverse("admin:content_leadershipmessage_changelist"))
        self.assertContains(response, "Test Leader")


class CategoryPhotoTests(TestCase):
    CATEGORY_SLUGS = [
        "dialysis",
        "urology",
        "interventional-cardiology",
        "anesthesia-respiratory-care",
        "gastroenterology-hepatobiliary",
        "neurosurgery",
        "interventional-radiology-biopsy",
        "general-surgery",
        "diagnostics-equipment",
        "hygiene-disinfection",
    ]

    def test_photo_files_exist_in_both_sizes(self):
        from pathlib import Path

        from django.conf import settings

        photo_dir = Path(settings.BASE_DIR) / "static" / "images" / "photos"
        expected = ["hero.webp", "hero-640.webp", "CREDITS.md"]
        for slug in self.CATEGORY_SLUGS:
            expected += [f"categories/{slug}.webp", f"categories/{slug}-480.webp"]
        for name in expected:
            with self.subTest(file=name):
                self.assertTrue((photo_dir / name).exists())

    def test_lookup_uses_own_then_parent_then_none(self):
        from apps.catalog.models import Category
        from apps.content.templatetags.site_tags import category_photo

        dialysis = Category(name="Dialysis", slug="dialysis")
        child = Category(name="Dialysis Needles", slug="dialysis-needles", parent=dialysis)
        unknown = Category(name="New Range", slug="new-range")

        photo = category_photo(dialysis)
        self.assertTrue(photo["src"].endswith("/images/photos/categories/dialysis.webp"))
        self.assertTrue(photo["src_small"].endswith("/images/photos/categories/dialysis-480.webp"))
        self.assertEqual(category_photo(child), photo)
        self.assertIsNone(category_photo(unknown))

    def test_cards_use_photo_or_fall_back_to_illustration(self):
        from apps.core.testing import make_category

        make_category("Dialysis")
        make_category("New Range")
        response = self.client.get(reverse("home"))

        self.assertContains(response, "/static/images/photos/categories/dialysis.webp")
        self.assertContains(response, "/static/images/categories/default.svg")

    def test_homepage_hero_photo(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "/static/images/photos/hero.webp")
        self.assertContains(response, 'alt="Healthcare worker taking supplies from a hospital supply room shelf"')

    def test_products_without_photos_keep_the_illustration(self):
        # A scene photo must never stand in for a product photo.
        from apps.core.testing import make_category, make_company, make_product

        product = make_product("Hollow Fiber Dialyzer", make_category("Dialysis"), make_company("Bain Medical"))
        response = self.client.get(product.get_absolute_url())
        self.assertContains(response, "/static/images/categories/dialysis.svg")
        self.assertNotContains(response, "/static/images/photos/categories/dialysis.webp")
