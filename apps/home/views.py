from django.db.models import Count, Prefetch, Q
from django.shortcuts import render

from apps.catalog.models import Category, Product
from apps.companies.models import Company
from apps.team.models import City, Territory


def home(request):
    public_products = Product.objects.public()

    context = {
        "partners": Company.objects.filter(
            is_official_partner=True,
            is_active=True,
        ),
        # Only categories that currently have something to show.
        "categories": (
            Category.objects.filter(is_active=True, parent__isnull=True)
            .annotate(
                product_count=Count(
                    "products",
                    filter=Q(products__in=public_products),
                    distinct=True,
                )
            )
            .filter(product_count__gt=0)
        ),
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
    }

    return render(
        request,
        "home/index.html",
        context,
    )
