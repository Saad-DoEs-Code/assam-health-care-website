"""
Small helpers for creating test data. Used by the test modules of each app.
"""

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
