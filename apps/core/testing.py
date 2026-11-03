"""
Small helpers for creating test data. Used by the test modules of each app.
"""

from django.test.runner import DiscoverRunner
from django.test.utils import override_settings

from apps.catalog.models import Category, Product, ProductVariant
from apps.companies.models import Company
from apps.team.models import City, Territory


def make_company(name="Bain Medical", **kwargs):
    defaults = {"slug": name.lower().replace(" ", "-"), "is_active": True}
    defaults.update(kwargs)
    return Company.objects.create(name=name, **defaults)


def make_category(name="Dialysis", **kwargs):
    defaults = {"slug": name.lower().replace(" ", "-"), "is_active": True}
    defaults.update(kwargs)
    return Category.objects.create(name=name, **defaults)


def make_product(name, category, company, **kwargs):
    defaults = {"slug": name.lower().replace(" ", "-"), "is_active": True}
    defaults.update(kwargs)
    return Product.objects.create(
        name=name, category=category, company=company, **defaults
    )


def make_variant(product, name, **kwargs):
    return ProductVariant.objects.create(product=product, name=name, **kwargs)


def make_city(name="Multan", territory_name="Multan & Central Punjab", **kwargs):
    territory, _ = Territory.objects.get_or_create(
        slug=territory_name.lower().replace(" ", "-").replace("&", "and"),
        defaults={"name": territory_name},
    )
    return City.objects.create(name=name, territory=territory, **kwargs)


class TestRunner(DiscoverRunner):
    """
    Runs the tests without a cache, so rate-limit counts from one test never
    affect another (rate-limit tests switch a real cache back on themselves),
    with a fast password hasher, so sign-in tests do not slow the suite, and
    with plain static URLs (no development ?v= suffix).
    """

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self._no_cache = override_settings(
            CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}},
            PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
            STORAGES={
                "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
                "staticfiles": {
                    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
                },
            },
        )
        self._no_cache.enable()

    def teardown_test_environment(self, **kwargs):
        self._no_cache.disable()
        super().teardown_test_environment(**kwargs)
