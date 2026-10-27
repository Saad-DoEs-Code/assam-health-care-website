from django.db.models import Count, Q
from django.shortcuts import render

from apps.catalog.models import Product

from .models import Company


def partner_list(request):
    public_products = Product.objects.public()

    companies = Company.objects.filter(is_active=True).annotate(
        product_count=Count(
            "products",
            filter=Q(products__in=public_products),
            distinct=True,
        )
    )

    context = {
        "partners": companies.filter(is_official_partner=True),
        # Other active suppliers are only listed when they have products on
        # the website, so the page never implies a relationship it can't show.
        "suppliers": companies.filter(is_official_partner=False, product_count__gt=0),
    }
    return render(request, "companies/partner_list.html", context)
