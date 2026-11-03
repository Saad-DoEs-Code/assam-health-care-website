from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.testing import make_category, make_city, make_company, make_product
from apps.inquiries.models import Inquiry, InquiryItem, WatchlistEntry
from apps.inquiries.screening import mark_as_competitor, screen_inquiry


class ScreeningTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.city = make_city("Multan")
        cls.company = make_company("Bain Medical")
        cls.categories = [make_category(f"Range {n}") for n in range(5)]
        cls.products = [
            make_product(f"Product {n}", cls.categories[n % 5], cls.company)
            for n in range(12)
        ]

    def make_inquiry(self, items=1, **kwargs):
        defaults = {
            "name": "Dr. Ayesha Khan",
            "organization_type": "hospital",
            "organization": "Nishtar Hospital",
            "designation": "Procurement Officer",
            "phone": "0300-1234567",
            "email": "procurement@nishtar.example",
            "city": self.city,
        }
        defaults.update(kwargs)
        inquiry = Inquiry.objects.create(**defaults)
        InquiryItem.objects.bulk_create(
            [InquiryItem(inquiry=inquiry, product=product, quantity=1) for product in self.products[:items]]
        )
        return screen_inquiry(inquiry)

    def add_watch(self, kind, value, **kwargs):
        return WatchlistEntry.objects.create(kind=kind, value=value, **kwargs)


class RiskRulesTests(ScreeningTestBase):
    def test_ordinary_hospital_request_is_low_risk(self):
        inquiry = self.make_inquiry()
        self.assertEqual(inquiry.risk_level, Inquiry.RISK_LOW)
        self.assertEqual(inquiry.risk_reason_list, [])

    def test_watchlisted_phone_matches_in_any_format(self):
        self.add_watch(WatchlistEntry.KIND_PHONE, "+92 300 123 4567", reason="Rival distributor")
        inquiry = self.make_inquiry(phone="03001234567")
        self.assertEqual(inquiry.risk_level, Inquiry.RISK_HIGH)
        self.assertIn("Rival distributor", inquiry.risk_reasons)

    def test_watchlisted_whatsapp_number_matches(self):
        self.add_watch(WatchlistEntry.KIND_PHONE, "0321-5550000")
        inquiry = self.make_inquiry(whatsapp="+923215550000")
        self.assertEqual(inquiry.risk_level, Inquiry.RISK_HIGH)

    def test_watchlisted_email_domain_organisation_and_keyword(self):
        cases = [
            (WatchlistEntry.KIND_EMAIL_DOMAIN, "@rival.example", {"email": "buyer@RIVAL.example"}),
            (WatchlistEntry.KIND_EMAIL, "spy@example.com", {"email": "Spy@Example.com"}),
            (WatchlistEntry.KIND_ORGANIZATION, "Rival Surgical", {"organization": "Rival Surgical Traders"}),
            (WatchlistEntry.KIND_KEYWORD, "price list", {"message": "Please share your full PRICE LIST."}),
        ]
        for kind, value, fields in cases:
            with self.subTest(kind=kind):
                WatchlistEntry.objects.all().delete()
                self.add_watch(kind, value)
                self.assertEqual(self.make_inquiry(**fields).risk_level, Inquiry.RISK_HIGH)

    def test_inactive_watchlist_entries_are_ignored(self):
        self.add_watch(WatchlistEntry.KIND_PHONE, "0300-1234567", is_active=False)
        self.assertEqual(self.make_inquiry().risk_level, Inquiry.RISK_LOW)

    def test_distributor_is_medium_risk(self):
        inquiry = self.make_inquiry(organization_type="distributor")
        self.assertEqual(inquiry.risk_level, Inquiry.RISK_MEDIUM)
        self.assertIn("distributor", inquiry.risk_reasons)

    def test_broad_request_is_medium_risk(self):
        inquiry = self.make_inquiry(items=10)
        self.assertEqual(inquiry.risk_level, Inquiry.RISK_MEDIUM)
        self.assertIn("Broad request", inquiry.risk_reasons)

    def test_distributor_with_broad_request_is_high_risk(self):
        inquiry = self.make_inquiry(items=10, organization_type="distributor")
        self.assertEqual(inquiry.risk_level, Inquiry.RISK_HIGH)

    def test_same_phone_under_different_name_is_flagged(self):
        self.make_inquiry(name="Ali Raza", organization="City Clinic")
        inquiry = self.make_inquiry(name="Bilal Ahmed", phone="+92 300 1234567")
        self.assertEqual(inquiry.risk_level, Inquiry.RISK_MEDIUM)
        self.assertIn("different name or organisation", inquiry.risk_reasons)

    def test_contact_previously_marked_competitor_is_high_risk(self):
        earlier = self.make_inquiry(email="someone@other.example", phone="0333-0000000")
        earlier.is_suspected_competitor = True
        earlier.save()
        inquiry = self.make_inquiry(email="someone@other.example", phone="0345-1111111")
        self.assertEqual(inquiry.risk_level, Inquiry.RISK_HIGH)

    def test_returning_customer_is_low_risk(self):
        earlier = self.make_inquiry(name="Old Name")
        earlier.status = "converted"
        earlier.save()
        inquiry = self.make_inquiry(email="new.address@gmail.com")
        self.assertTrue(inquiry.is_returning_customer)
        self.assertEqual(inquiry.risk_level, Inquiry.RISK_LOW)
        self.assertIn("Returning customer", inquiry.risk_reasons)

    def test_free_email_is_noted_but_stays_low(self):
        inquiry = self.make_inquiry(email="buyer@gmail.com")
        self.assertEqual(inquiry.risk_level, Inquiry.RISK_LOW)
        self.assertIn("Free email address", inquiry.risk_reasons)

    def test_frequent_requests_are_noted(self):
        old = self.make_inquiry()
        Inquiry.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=60))
        self.make_inquiry()
        self.make_inquiry()
        inquiry = self.make_inquiry()
        self.assertIn("3 requests from this contact", inquiry.risk_reasons)

    def test_watchlist_values_are_unique_after_normalisation(self):
        from django.db import IntegrityError, transaction

        self.add_watch(WatchlistEntry.KIND_PHONE, "0300-1234567")
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.add_watch(WatchlistEntry.KIND_PHONE, "+92 300 1234567")


class MarkAsCompetitorTests(ScreeningTestBase):
    def test_closes_inquiry_and_watchlists_identifiers(self):
        inquiry = self.make_inquiry(whatsapp="0321-9999999")
        added = mark_as_competitor(inquiry)

        inquiry.refresh_from_db()
        self.assertTrue(inquiry.is_suspected_competitor)
        self.assertEqual(inquiry.status, "closed")
        self.assertEqual(inquiry.risk_level, Inquiry.RISK_HIGH)
        self.assertEqual(added, 4)  # phone, WhatsApp, email, organisation
        self.assertEqual(mark_as_competitor(inquiry), 0)  # no duplicates

    def test_later_attempts_are_flagged(self):
        mark_as_competitor(self.make_inquiry())
        later = self.make_inquiry(name="Different Person", email="other@x.example", phone="0300 123 4567")
        self.assertEqual(later.risk_level, Inquiry.RISK_HIGH)


class PublicFormScreeningTests(ScreeningTestBase):
    url = reverse("create_inquiry")

    def post(self, with_product=True, **overrides):
        data = {
            "name": "Dr. Ayesha Khan",
            "organization_type": "hospital",
            "organization": "Nishtar Hospital",
            "designation": "Procurement Officer",
            "phone": "0300-1234567",
            "email": "",
            "whatsapp": "",
            "city": str(self.city.pk),
            "message": "",
            "website": "",
            "items-TOTAL_FORMS": "1" if with_product else "0",
            "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "0",
            "items-MAX_NUM_FORMS": "50",
        }
        if with_product:
            data.update({
                "items-0-product": str(self.products[0].pk),
                "items-0-variant": "",
                "items-0-quantity": "5",
                "items-0-notes": "",
            })
        data.update(overrides)
        return self.client.post(self.url, data)

    def test_organisation_type_is_required(self):
        response = self.post(organization_type="")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_organisation_and_designation_required_for_quotations(self):
        response = self.post(organization="", designation="")
        self.assertContains(response, "This field is required when requesting a quotation.", count=2)
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_general_message_does_not_need_organisation(self):
        response = self.post(with_product=False, organization="", designation="", message="Do you supply gloves?")
        self.assertRedirects(response, reverse("inquiry_success"))

    def test_submission_is_screened(self):
        self.post(organization_type="distributor")
        self.assertEqual(Inquiry.objects.get().risk_level, Inquiry.RISK_MEDIUM)

    def test_flagged_requester_sees_normal_confirmation(self):
        WatchlistEntry.objects.create(kind=WatchlistEntry.KIND_PHONE, value="0300-1234567")
        response = self.post(follow=False)
        self.assertRedirects(response, reverse("inquiry_success"))
        page = self.client.get(reverse("inquiry_success")).content.decode().lower()
        for word in ["risk", "watchlist", "competitor", "flag"]:
            self.assertNotIn(word, page)


class AdminVerificationTests(ScreeningTestBase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("sales", "sales@example.com", "test-password-123")
        self.client.force_login(self.user)
        self.inquiry = self.make_inquiry()
        self.url = reverse("admin:inquiries_inquiry_change", args=[self.inquiry.pk])

    def change_data(self, **overrides):
        data = {
            "name": self.inquiry.name,
            "designation": self.inquiry.designation,
            "organization": self.inquiry.organization,
            "organization_type": self.inquiry.organization_type,
            "phone": self.inquiry.phone,
            "whatsapp": "",
            "email": self.inquiry.email,
            "city": str(self.city.pk),
            "message": "",
            "verification_note": "",
            "status": "new",
            "assigned_employee": "",
            "items-TOTAL_FORMS": "0",
            "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "0",
            "items-MAX_NUM_FORMS": "1000",
        }
        for item in self.inquiry.items.all():
            index = int(data["items-TOTAL_FORMS"])
            data.update({
                f"items-{index}-id": str(item.pk),
                f"items-{index}-inquiry": str(self.inquiry.pk),
                f"items-{index}-product": str(item.product_id),
                f"items-{index}-variant": "",
                f"items-{index}-quantity": str(item.quantity),
                f"items-{index}-notes": "",
            })
            data["items-TOTAL_FORMS"] = str(index + 1)
            data["items-INITIAL_FORMS"] = str(index + 1)
        data.update(overrides)
        return data

    def test_cannot_mark_quoted_without_verification(self):
        response = self.client.post(self.url, self.change_data(status="quoted"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "before marking the inquiry as quoted")
        self.inquiry.refresh_from_db()
        self.assertEqual(self.inquiry.status, "new")

    def test_verification_needs_a_note(self):
        response = self.client.post(self.url, self.change_data(is_verified="on"))
        self.assertContains(response, "Note how the requester was verified")

    def test_verifying_records_user_and_time_then_allows_quoting(self):
        response = self.client.post(
            self.url,
            self.change_data(is_verified="on", verification_note="Called hospital landline", status="quoted"),
        )
        self.assertEqual(response.status_code, 302)
        self.inquiry.refresh_from_db()
        self.assertTrue(self.inquiry.is_verified)
        self.assertEqual(self.inquiry.verified_by, self.user)
        self.assertIsNotNone(self.inquiry.verified_at)
        self.assertEqual(self.inquiry.status, "quoted")

    def test_change_page_shows_risk_reasons(self):
        WatchlistEntry.objects.create(kind=WatchlistEntry.KIND_PHONE, value="0300-1234567", reason="Known rival")
        screen_inquiry(self.inquiry)
        response = self.client.get(self.url)
        self.assertContains(response, "Known rival")
        self.assertContains(response, "High")

    def test_mark_competitor_action(self):
        changelist = reverse("admin:inquiries_inquiry_changelist")
        response = self.client.post(changelist, {
            "action": "mark_as_suspected_competitor",
            "_selected_action": [self.inquiry.pk],
        })
        self.assertEqual(response.status_code, 302)
        self.inquiry.refresh_from_db()
        self.assertTrue(self.inquiry.is_suspected_competitor)
        self.assertTrue(WatchlistEntry.objects.filter(source_inquiry=self.inquiry).exists())

    def test_list_filters_by_risk(self):
        response = self.client.get(reverse("admin:inquiries_inquiry_changelist"), {"risk_level__exact": "high"})
        self.assertEqual(response.status_code, 200)

    def test_watchlist_admin_page(self):
        WatchlistEntry.objects.create(kind=WatchlistEntry.KIND_ORGANIZATION, value="Rival Traders")
        response = self.client.get(reverse("admin:inquiries_watchlistentry_changelist"))
        self.assertContains(response, "Rival Traders")
