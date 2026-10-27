from django.test import TestCase
from django.urls import reverse

from apps.core.testing import make_city
from apps.team.models import Employee, Territory


class TeamPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.city = make_city("Multan")
        cls.territory = cls.city.territory
        make_city("Hidden Town", territory_name="Multan & Central Punjab", is_active=False)
        Territory.objects.create(name="Closed Territory", slug="closed", is_active=False)

        cls.visible = Employee.objects.create(
            name="Anas Abdullah", designation="Sales Manager",
            phone="03001112222", email="anas@example.com",
        )
        cls.visible.territories.add(cls.territory)

        Employee.objects.create(
            name="Internal Accountant", designation="Accounts",
            phone="03003334444", display_on_website=False,
        )
        Employee.objects.create(
            name="Former Rep", designation="Sales", phone="03005556666", is_active=False,
        )

    def test_only_visible_active_employees_are_shown(self):
        response = self.client.get(reverse("team"))

        self.assertContains(response, "Anas Abdullah")
        self.assertNotContains(response, "Internal Accountant")
        self.assertNotContains(response, "03003334444")
        self.assertNotContains(response, "Former Rep")

    def test_territories_and_active_cities_are_shown(self):
        response = self.client.get(reverse("team"))

        self.assertContains(response, "Multan &amp; Central Punjab")
        self.assertContains(response, "Multan")
        self.assertNotContains(response, "Hidden Town")
        self.assertNotContains(response, "Closed Territory")

    def test_phone_link_uses_international_format(self):
        response = self.client.get(reverse("team"))
        self.assertContains(response, 'href="tel:+923001112222"')

    def test_missing_photo_uses_placeholder(self):
        response = self.client.get(reverse("team"))
        self.assertContains(response, "employee-card__photo--placeholder")

    def test_empty_team_shows_contact_alternative(self):
        Employee.objects.update(display_on_website=False)
        response = self.client.get(reverse("team"))
        self.assertContains(response, "put you in touch")
