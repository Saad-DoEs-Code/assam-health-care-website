import re

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.careers.models import Job, JobApplication
from apps.core import ratelimit
from apps.core.testing import (
    make_category,
    make_city,
    make_company,
    make_product,
    make_variant,
)
from apps.inquiries.forms import InquiryItemForm, get_quote_catalogue
from apps.inquiries.models import Inquiry, WatchlistEntry

# The test runner disables the cache; these tests need real counters.
LOCAL_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "rate-limit-tests",
    }
}


@override_settings(CACHES=LOCAL_CACHE)
class RateLimitTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.city = make_city("Multan")

    def setUp(self):
        cache.clear()

    def inquiry_data(self, **overrides):
        data = {
            "name": "Dr. Ayesha Khan",
            "organization_type": "hospital",
            "phone": "0300-1234567",
            "city": str(self.city.pk),
            "message": "Please call me about dialysis supplies.",
            "website": "",
            "items-TOTAL_FORMS": "0",
            "items-INITIAL_FORMS": "0",
        }
        data.update(overrides)
        return data


class InquiryRateLimitTests(RateLimitTestBase):
    def test_requests_beyond_the_limit_are_refused_and_not_saved(self):
        attempts, _window = ratelimit.INQUIRY_LIMIT
        for _ in range(attempts):
            response = self.client.post(reverse("create_inquiry"), self.inquiry_data())
            self.assertRedirects(response, reverse("inquiry_success"))

        response = self.client.post(reverse("create_inquiry"), self.inquiry_data())

        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Too many requests", status_code=429)
        self.assertEqual(Inquiry.objects.count(), attempts)

    def test_failed_validation_does_not_use_up_the_limit(self):
        attempts, _window = ratelimit.INQUIRY_LIMIT
        for _ in range(attempts + 5):
            self.client.post(reverse("create_inquiry"), self.inquiry_data(phone="123"))

        response = self.client.post(reverse("create_inquiry"), self.inquiry_data())

        self.assertRedirects(response, reverse("inquiry_success"))

    def test_honeypot_submissions_count_towards_the_limit(self):
        attempts, _window = ratelimit.INQUIRY_LIMIT
        for _ in range(attempts):
            self.client.post(reverse("create_inquiry"), self.inquiry_data(website="spam"))

        response = self.client.post(reverse("create_inquiry"), self.inquiry_data())

        self.assertEqual(response.status_code, 429)
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_limit_is_per_ip_address(self):
        attempts, _window = ratelimit.INQUIRY_LIMIT
        for _ in range(attempts):
            self.client.post(
                reverse("create_inquiry"), self.inquiry_data(), REMOTE_ADDR="10.0.0.1"
            )

        response = self.client.post(
            reverse("create_inquiry"), self.inquiry_data(), REMOTE_ADDR="10.0.0.2"
        )

        self.assertRedirects(response, reverse("inquiry_success"))

    def test_x_real_ip_is_ignored_unless_behind_proxy(self):
        # Without a proxy, a visitor could rotate this header to dodge the limit.
        attempts, _window = ratelimit.INQUIRY_LIMIT
        for index in range(attempts):
            self.client.post(
                reverse("create_inquiry"),
                self.inquiry_data(),
                HTTP_X_REAL_IP=f"203.0.113.{index}",
            )

        response = self.client.post(
            reverse("create_inquiry"), self.inquiry_data(), HTTP_X_REAL_IP="203.0.113.99"
        )

        self.assertEqual(response.status_code, 429)

    @override_settings(SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https"))
    def test_x_real_ip_from_nginx_identifies_visitors_behind_proxy(self):
        attempts, _window = ratelimit.INQUIRY_LIMIT
        for _ in range(attempts):
            self.client.post(
                reverse("create_inquiry"), self.inquiry_data(), HTTP_X_REAL_IP="203.0.113.1"
            )

        blocked = self.client.post(
            reverse("create_inquiry"), self.inquiry_data(), HTTP_X_REAL_IP="203.0.113.1"
        )
        other_visitor = self.client.post(
            reverse("create_inquiry"), self.inquiry_data(), HTTP_X_REAL_IP="203.0.113.2"
        )

        self.assertEqual(blocked.status_code, 429)
        self.assertRedirects(other_visitor, reverse("inquiry_success"))


class JobApplicationRateLimitTests(RateLimitTestBase):
    def test_applications_beyond_the_limit_are_refused(self):
        job = Job.objects.create(
            title="Sales Officer", slug="sales-officer", description="d", is_published=True
        )
        data = {
            "name": "Ali Raza",
            "email": "ali@example.com",
            "phone": "0301-7654321",
            "website": "",
        }
        attempts, _window = ratelimit.JOB_APPLICATION_LIMIT
        for _ in range(attempts):
            self.client.post(job.get_absolute_url(), data)

        response = self.client.post(job.get_absolute_url(), data)

        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Too many requests", status_code=429)
        self.assertEqual(JobApplication.objects.count(), attempts)


class AdminLoginRateLimitTests(RateLimitTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        get_user_model().objects.create_superuser("owner", "owner@example.com", "correct-horse-9")

    def login(self, password, **extra):
        return self.client.post(
            reverse("admin_login"),
            {"username": "owner", "password": password, "next": "/"},
            **extra,
        )

    def test_sign_in_pauses_after_repeated_wrong_passwords(self):
        attempts, _window = ratelimit.ADMIN_LOGIN_FAILURE_LIMIT
        for index in range(attempts):
            self.assertEqual(self.login(f"wrong-{index}").status_code, 200)

        # Even the right password is refused while paused.
        response = self.login("correct-horse-9")

        self.assertContains(response, "Sign-in is paused", status_code=429)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_correct_password_works_before_the_limit(self):
        for index in range(3):
            self.login(f"wrong-{index}")

        response = self.login("correct-horse-9")

        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_other_ip_addresses_can_still_sign_in(self):
        attempts, _window = ratelimit.ADMIN_LOGIN_FAILURE_LIMIT
        for index in range(attempts):
            self.login(f"wrong-{index}", REMOTE_ADDR="10.0.0.9")

        response = self.login("correct-horse-9", REMOTE_ADDR="10.0.0.10")

        self.assertEqual(response.status_code, 302)

    def test_admin_index_redirects_to_rate_limited_login(self):
        response = self.client.get(reverse("admin:index"))
        self.assertRedirects(
            response, f"{reverse('admin_login')}?next={reverse('admin:index')}"
        )


class SecurityHeaderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        make_city("Multan")

    def test_pages_send_a_content_security_policy(self):
        for url in (reverse("home"), reverse("create_inquiry"), reverse("product_list")):
            with self.subTest(url=url):
                policy = self.client.get(url)["Content-Security-Policy"]
                self.assertIn("script-src 'self'", policy)
                self.assertIn("object-src 'none'", policy)
                self.assertIn("frame-ancestors 'none'", policy)

    def test_pages_have_no_inline_scripts_the_policy_would_block(self):
        for url in (reverse("home"), reverse("create_inquiry"), reverse("about")):
            with self.subTest(url=url):
                html = self.client.get(url).content.decode()
                for tag in re.findall(r"<script\b[^>]*>", html):
                    self.assertTrue(
                        "src=" in tag or 'type="application/json"' in tag,
                        f"Inline script would be blocked by CSP: {tag}",
                    )

    def test_form_pages_reject_other_http_methods(self):
        response = self.client.put(reverse("create_inquiry"))
        self.assertEqual(response.status_code, 405)


class PhoneDigitTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.city = make_city("Multan")

    def test_urdu_digits_are_saved_as_ascii_and_match_the_watchlist(self):
        WatchlistEntry.objects.create(
            kind=WatchlistEntry.KIND_PHONE, value="0300-1234567", reason="Competitor"
        )

        self.client.post(
            reverse("create_inquiry"),
            {
                "name": "Test",
                "organization_type": "hospital",
                # ۰۳۰۰-۱۲۳۴۵۶۷ typed on an Urdu keyboard
                "phone": "۰۳۰۰-۱۲۳۴۵۶۷",
                "city": str(self.city.pk),
                "message": "Rates please",
                "items-TOTAL_FORMS": "0",
                "items-INITIAL_FORMS": "0",
            },
        )

        inquiry = Inquiry.objects.get()
        self.assertEqual(inquiry.phone, "0300-1234567")
        self.assertEqual(inquiry.phone_normalized, "+923001234567")
        self.assertEqual(inquiry.risk_level, Inquiry.RISK_HIGH)


class QuickSelectTests(TestCase):
    def test_product_and_variant_names_are_escaped(self):
        company = make_company("Acme")
        category = make_category("Dialysis")
        product = make_product('<script>alert("x")</script>', category, company)
        make_variant(product, "<b>Large</b>")

        form = InquiryItemForm(prefix="items-0", catalogue=get_quote_catalogue())
        html = str(form["product"]) + str(form["variant"])

        self.assertNotIn("<script>", html)
        self.assertNotIn("<b>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_submitted_choice_stays_selected(self):
        company = make_company("Acme")
        category = make_category("Dialysis")
        product = make_product("Dialyzer", category, company)
        variant = make_variant(product, "16-PF")

        form = InquiryItemForm(
            {
                "items-0-product": str(product.pk),
                "items-0-variant": str(variant.pk),
                "items-0-quantity": "2",
            },
            prefix="items-0",
            catalogue=get_quote_catalogue(),
        )

        self.assertIn(f'<option value="{variant.pk}" selected>', str(form["variant"]))
        self.assertIn(f'<option value="{product.pk}" selected>', str(form["product"]))


class VersionedStaticUrlTests(TestCase):
    def test_development_static_urls_change_when_the_file_changes(self):
        from apps.core.storage import VersionedStaticFilesStorage

        storage = VersionedStaticFilesStorage()

        self.assertRegex(storage.url("css/site.css"), r"^/static/css/site\.css\?v=\d+$")
        self.assertEqual(storage.url("no/such/file.css"), "/static/no/such/file.css")
