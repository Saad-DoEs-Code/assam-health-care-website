from django.db.models import Count, Prefetch, Q
from django.shortcuts import render

from apps.catalog.models import Category, Product
from apps.companies.models import Company
from apps.team.models import City, Territory
from apps.team.views import public_employees


def home(request):
    public_products = Product.objects.public()

    # Every active top-level category is shown, with its count of products
    # currently listed online (categories may be listed before products are).
    categories = list(
        Category.objects.filter(is_active=True, parent__isnull=True).annotate(
            product_count=Count(
                "products",
                filter=Q(products__in=public_products),
                distinct=True,
            )
        )
    )

    context = {
        "partners": Company.objects.filter(
            is_official_partner=True,
            is_active=True,
        ),
        "categories": categories,
        "hero_categories": categories[:3],
        "featured_products": (
            public_products.filter(is_featured=True)
            .select_related("category", "company")
            .prefetch_related("images")[:6]
        ),
        "territories": Territory.objects.filter(is_active=True).prefetch_related(
            Prefetch(
                "cities",
                queryset=City.objects.filter(is_active=True),
                to_attr="active_cities",
            )
        ),
        "team_preview": public_employees()[:3],
    }

    return render(
        request,
        "home/index.html",
        context,
    )
