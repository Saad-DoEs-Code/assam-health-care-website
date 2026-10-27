from django.test import Client, TestCase
from django.urls import reverse

from apps.core.testing import (
    make_category,
    make_city,
    make_company,
    make_product,
    make_variant,
)
from apps.inquiries.forms import FALLBACK_BLANK_ROWS, MAX_INQUIRY_ITEMS
from apps.inquiries.models import Inquiry, InquiryItem


class InquiryTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = make_company("Bain Medical")
        cls.category = make_category("Dialysis")
        cls.dialyzer = make_product("Hollow Fiber Dialyzer", cls.category, cls.company)
        cls.size_14 = make_variant(cls.dialyzer, "14-PF")
        cls.size_16 = make_variant(cls.dialyzer, "16-PF")
        cls.bloodline = make_product("Blood Line Set", cls.category, cls.company)
        cls.city = make_city("Multan")

        cls.other_product = make_product("Catheter", cls.category, cls.company)
        cls.other_variant = make_variant(cls.other_product, "Large")

        cls.url = reverse("create_inquiry")

    def contact_data(self, **overrides):
        data = {
            "name": "Dr. Ayesha Khan",
            "organization": "Nishtar Hospital",
            "designation": "Procurement Officer",
            "phone": "0300-1234567",
            "whatsapp": "",
            "email": "ayesha@example.com",
            "city": str(self.city.pk),
            "message": "",
            "website": "",
            "submission_token": "",
        }
        data.update(overrides)
        return data

    def post_data(self, items, extra_rows=0, **contact_overrides):
        """
        Build POST data like the browser sends it. `items` is a list of dicts
        with product/variant/quantity/notes; `extra_rows` adds blank rows like
        the no-JavaScript fallback.
        """
        data = self.contact_data(**contact_overrides)
        rows = list(items) + [{} for _ in range(extra_rows)]
        data.update(
            {
                "items-TOTAL_FORMS": str(len(rows)),
                "items-INITIAL_FORMS": "0",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": str(MAX_INQUIRY_ITEMS),
            }
        )
        for index, row in enumerate(rows):
            data[f"items-{index}-product"] = str(row.get("product", ""))
            data[f"items-{index}-variant"] = str(row.get("variant", ""))
            data[f"items-{index}-quantity"] = str(row.get("quantity", "1"))
            data[f"items-{index}-notes"] = row.get("notes", "")
            if row.get("delete"):
                data[f"items-{index}-DELETE"] = "on"
        return data


class InquiryFormPageTests(InquiryTestBase):
    def test_form_loads_without_preselected_product(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "data-product-id=")
        # Blank rows for visitors without JavaScript.
        self.assertContains(response, "data-blank-row", count=FALLBACK_BLANK_ROWS)
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_product_is_preselected_from_query_parameter(self):
        response = self.client.get(self.url, {"product": self.dialyzer.pk})

        self.assertContains(response, f'data-product-id="{self.dialyzer.pk}"')
        self.assertContains(response, "Hollow Fiber Dialyzer")
        # Its variants are offered in the row.
        self.assertContains(response, "14-PF")

    def test_malformed_product_parameter_is_ignored(self):
        for value in ["abc", "-1", "1 OR 1=1", "999999", ""]:
            response = self.client.get(self.url, {"product": value})
            self.assertEqual(response.status_code, 200, value)
            self.assertNotContains(response, "data-product-id=")

    def test_inactive_product_is_not_preselected(self):
        self.dialyzer.is_active = False
        self.dialyzer.save()

        response = self.client.get(self.url, {"product": self.dialyzer.pk})

        self.assertNotContains(response, f'data-product-id="{self.dialyzer.pk}"')

    def test_catalogue_data_only_contains_public_products(self):
        hidden = make_product(
            "Hidden Product",
            self.category,
            make_company("Inactive Co", is_active=False),
        )

        response = self.client.get(self.url)
        catalogue_ids = {item["id"] for item in response.context["catalogue_data"]}

        self.assertIn(self.dialyzer.pk, catalogue_ids)
        self.assertNotIn(hidden.pk, catalogue_ids)

    def test_only_active_cities_are_offered(self):
        make_city("Inactive Town", is_active=False)

        response = self.client.get(self.url)
        cities = list(response.context["form"].fields["city"].queryset)

        self.assertEqual(cities, [self.city])


class InquirySubmissionTests(InquiryTestBase):
    def test_multiple_products_create_one_inquiry_with_items(self):
        data = self.post_data(
            [
                {"product": self.dialyzer.pk, "variant": self.size_14.pk, "quantity": 500, "notes": "Urgent"},
                {"product": self.dialyzer.pk, "variant": self.size_16.pk, "quantity": 1500},
                {"product": self.bloodline.pk, "quantity": 20},
            ],
            extra_rows=2,
        )

        response = self.client.post(self.url, data)

        self.assertRedirects(response, reverse("inquiry_success"))
        self.assertEqual(Inquiry.objects.count(), 1)

        inquiry = Inquiry.objects.get()
        self.assertEqual(inquiry.name, "Dr. Ayesha Khan")
        self.assertEqual(inquiry.city, self.city)

        items = list(inquiry.items.order_by("id"))
        self.assertEqual(len(items), 3)
        self.assertEqual(
            [(i.product, i.variant, i.quantity, i.notes) for i in items],
            [
                (self.dialyzer, self.size_14, 500, "Urgent"),
                (self.dialyzer, self.size_16, 1500, ""),
                (self.bloodline, None, 20, ""),
            ],
        )

    def test_success_page_shows_summary_of_own_inquiry(self):
        data = self.post_data([{"product": self.bloodline.pk, "quantity": 7}])

        response = self.client.post(self.url, data, follow=True)

        inquiry = Inquiry.objects.get()
        self.assertContains(response, f"#{inquiry.pk}")
        self.assertContains(response, "Blood Line Set")
        self.assertContains(response, "Qty 7")

    def test_success_page_without_session_shows_generic_message(self):
        response = self.client.get(reverse("inquiry_success"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thank You for Your Request")
        self.assertNotContains(response, "Reference number")

    def test_message_only_inquiry_is_accepted(self):
        data = self.post_data([], extra_rows=3, message="Please call me about gloves.")

        response = self.client.post(self.url, data)

        self.assertRedirects(response, reverse("inquiry_success"))
        self.assertEqual(Inquiry.objects.get().items.count(), 0)

    def test_empty_request_without_products_or_message_is_rejected(self):
        data = self.post_data([], extra_rows=3)

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please add at least one product")
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_deleted_rows_are_ignored(self):
        data = self.post_data(
            [
                {"product": self.dialyzer.pk, "quantity": 1, "delete": True},
                {"product": self.bloodline.pk, "quantity": 2},
            ]
        )

        self.client.post(self.url, data)

        items = InquiryItem.objects.all()
        self.assertEqual([item.product for item in items], [self.bloodline])

    def test_rows_removed_from_page_are_ignored(self):
        # JavaScript removes rows from the page without renumbering, so
        # indexes can have gaps up to TOTAL_FORMS.
        data = self.post_data(
            [{"product": self.dialyzer.pk}, {"product": self.bloodline.pk}]
        )
        for field in ("product", "variant", "quantity", "notes"):
            del data[f"items-0-{field}"]

        response = self.client.post(self.url, data)

        self.assertRedirects(response, reverse("inquiry_success"))
        self.assertEqual(
            [item.product for item in InquiryItem.objects.all()], [self.bloodline]
        )


class InquiryValidationTests(InquiryTestBase):
    def assert_rejected(self, data, expected_text=None):
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        if expected_text:
            self.assertContains(response, expected_text)
        self.assertEqual(Inquiry.objects.count(), 0)
        self.assertEqual(InquiryItem.objects.count(), 0)
        return response

    def test_variant_must_belong_to_product(self):
        data = self.post_data(
            [{"product": self.dialyzer.pk, "variant": self.other_variant.pk}]
        )
        self.assert_rejected(data, "does not belong to the selected product")

    def test_inactive_variant_is_rejected(self):
        self.size_14.is_active = False
        self.size_14.save()
        data = self.post_data(
            [{"product": self.dialyzer.pk, "variant": self.size_14.pk}]
        )
        self.assert_rejected(data, "Select one of the available variants")

    def test_inactive_product_is_rejected(self):
        self.bloodline.is_active = False
        self.bloodline.save()
        data = self.post_data([{"product": self.bloodline.pk}])
        self.assert_rejected(data, "This product is not available")

    def test_product_in_inactive_category_is_rejected(self):
        hidden_category = make_category("Archived", is_active=False)
        product = make_product("Old Product", hidden_category, self.company)
        self.assert_rejected(self.post_data([{"product": product.pk}]))

    def test_product_from_inactive_company_is_rejected(self):
        company = make_company("Former Supplier", is_active=False)
        product = make_product("Old Supplier Product", self.category, company)
        self.assert_rejected(self.post_data([{"product": product.pk}]))

    def test_malformed_and_forged_product_ids_are_rejected(self):
        for bad_value in ["abc", "999999", "1.5", "<script>"]:
            with self.subTest(bad_value=bad_value):
                data = self.post_data([{"product": bad_value}])
                self.assert_rejected(data)

    def test_quantity_must_be_positive_integer(self):
        for bad_quantity in ["0", "-5", "abc", "2.5", "", "100000000"]:
            with self.subTest(quantity=bad_quantity):
                data = self.post_data(
                    [{"product": self.bloodline.pk, "quantity": bad_quantity}]
                )
                self.assert_rejected(data)

    def test_notes_length_is_limited(self):
        data = self.post_data([{"product": self.bloodline.pk, "notes": "x" * 301}])
        self.assert_rejected(data)

    def test_duplicate_product_and_variant_is_rejected(self):
        data = self.post_data(
            [
                {"product": self.dialyzer.pk, "variant": self.size_14.pk},
                {"product": self.dialyzer.pk, "variant": self.size_14.pk},
            ]
        )
        self.assert_rejected(data, "listed more than once")

    def test_duplicate_product_without_variant_is_rejected(self):
        data = self.post_data(
            [{"product": self.bloodline.pk}, {"product": self.bloodline.pk}]
        )
        self.assert_rejected(data, "listed more than once")

    def test_same_product_with_different_variants_is_allowed(self):
        data = self.post_data(
            [
                {"product": self.dialyzer.pk, "variant": self.size_14.pk},
                {"product": self.dialyzer.pk, "variant": self.size_16.pk},
            ]
        )
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse("inquiry_success"))
        self.assertEqual(InquiryItem.objects.count(), 2)

    def test_too_many_items_are_rejected(self):
        products = [
            make_product(f"Bulk Product {n}", self.category, self.company)
            for n in range(MAX_INQUIRY_ITEMS + 1)
        ]
        data = self.post_data([{"product": product.pk} for product in products])
        self.assert_rejected(data)

    def test_forged_total_forms_is_rejected_safely(self):
        data = self.post_data([{"product": self.bloodline.pk}])
        data["items-TOTAL_FORMS"] = "100000"
        self.assert_rejected(data)

    def test_missing_management_form_is_rejected_safely(self):
        data = self.contact_data()
        self.assert_rejected(data)

    def test_invalid_contact_details_keep_selected_products(self):
        data = self.post_data(
            [{"product": self.dialyzer.pk, "variant": self.size_16.pk, "quantity": 42}],
            phone="12",
            name="",
        )

        response = self.assert_rejected(data, "Enter a valid phone number")

        # The selected product row and its values are shown again.
        self.assertContains(response, f'data-product-id="{self.dialyzer.pk}"')
        self.assertContains(response, 'value="42"')
        self.assertContains(response, "This field is required")
        self.assertContains(response, 'value="Nishtar Hospital"')

    def test_invalid_item_prevents_partial_save(self):
        data = self.post_data(
            [
                {"product": self.bloodline.pk, "quantity": 3},
                {"product": self.dialyzer.pk, "variant": self.other_variant.pk},
            ]
        )
        self.assert_rejected(data)

    def test_inactive_city_is_rejected(self):
        inactive_city = make_city("Old City", is_active=False)
        data = self.post_data([{"product": self.bloodline.pk}], city=inactive_city.pk)
        self.assert_rejected(data)

    def test_get_request_does_not_create_inquiry(self):
        self.client.get(self.url, self.post_data([{"product": self.bloodline.pk}]))
        self.assertEqual(Inquiry.objects.count(), 0)


class InquiryAbuseProtectionTests(InquiryTestBase):
    def test_honeypot_submission_is_discarded(self):
        data = self.post_data([{"product": self.bloodline.pk}], website="http://spam.example")

        response = self.client.post(self.url, data)

        self.assertRedirects(response, reverse("inquiry_success"))
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_resubmitting_same_token_does_not_duplicate(self):
        data = self.post_data([{"product": self.bloodline.pk}], submission_token="abc123")

        self.client.post(self.url, data)
        response = self.client.post(self.url, data)

        self.assertRedirects(response, reverse("inquiry_success"))
        self.assertEqual(Inquiry.objects.count(), 1)

    def test_csrf_protection_is_enforced(self):
        csrf_client = Client(enforce_csrf_checks=True)
        data = self.post_data([{"product": self.bloodline.pk}])

        response = csrf_client.post(self.url, data)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Inquiry.objects.count(), 0)


class InquiryAdminTests(InquiryTestBase):
    def test_admin_change_page_lists_every_item(self):
        from django.contrib.auth import get_user_model

        admin_user = get_user_model().objects.create_superuser(
            "staff", "staff@example.com", "test-password-123"
        )
        self.client.force_login(admin_user)
        self.client.post(
            self.url,
            self.post_data(
                [
                    {"product": self.dialyzer.pk, "variant": self.size_14.pk, "quantity": 5, "notes": "Boxed"},
                    {"product": self.bloodline.pk, "quantity": 9},
                ]
            ),
        )
        inquiry = Inquiry.objects.get()

        changelist = self.client.get(reverse("admin:inquiries_inquiry_changelist"))
        change = self.client.get(
            reverse("admin:inquiries_inquiry_change", args=[inquiry.pk])
        )

        self.assertContains(changelist, "Dr. Ayesha Khan")
        self.assertContains(change, "Hollow Fiber Dialyzer")
        self.assertContains(change, "Blood Line Set")
        self.assertContains(change, "Boxed")
        self.assertContains(change, "Nishtar Hospital")

    def test_admin_requires_staff_login(self):
        response = self.client.get(reverse("admin:inquiries_inquiry_changelist"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response["Location"])
