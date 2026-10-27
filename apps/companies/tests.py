from django.test import TestCase
from django.urls import reverse

from apps.core.testing import make_category, make_company, make_product


class PartnerPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = make_category("Dialysis")
        cls.partner = make_company("Bain Medical", is_official_partner=True)
        cls.supplier = make_company("Generic Supplier")
        make_company("Supplier Without Products")
        make_company("Inactive Partner", is_official_partner=True, is_active=False)
        make_product("Hollow Fiber Dialyzer", category, cls.partner)
        make_product("Gauze Roll", category, cls.supplier)

    def test_official_partners_and_suppliers_are_separated(self):
        response = self.client.get(reverse("partners"))

        self.assertEqual(list(response.context["partners"]), [self.partner])
        self.assertEqual(list(response.context["suppliers"]), [self.supplier])
        self.assertNotContains(response, "Inactive Partner")
        self.assertNotContains(response, "Supplier Without Products")

    def test_partner_badge_only_on_official_partners(self):
        response = self.client.get(reverse("partners"))
        self.assertContains(
            response, '<span class="badge">Official distribution partner</span>', count=1
        )

    def test_links_to_company_products(self):
        response = self.client.get(reverse("partners"))
        self.assertContains(response, f"{reverse('product_list')}?company=bain-medical")
