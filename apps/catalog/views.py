from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404

from apps.companies.models import Company

from .models import Category, Product

PRODUCTS_PER_PAGE = 12


def product_list(request):
    products = (
        Product.objects.public()
        .select_related("category", "company")
        .prefetch_related("images")
    )

    search_query = request.GET.get("q", "").strip()[:100]
    category_slug = request.GET.get("category", "").strip()
    company_slug = request.GET.get("company", "").strip()

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(short_description__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(company__name__icontains=search_query)
            | Q(variants__name__icontains=search_query, variants__is_active=True)
        ).distinct()

    selected_category = None
    if category_slug:
        selected_category = Category.objects.filter(
            slug=category_slug, is_active=True
        ).first()
        if selected_category:
            # Include products from direct subcategories of the chosen one.
            products = products.filter(
                Q(category=selected_category)
                | Q(category__parent=selected_category)
            )
        else:
            # Unknown or inactive category: show nothing rather than everything.
            products = products.none()

    selected_company = None
    if company_slug:
        selected_company = Company.objects.filter(
            slug=company_slug, is_active=True
        ).first()
        products = (
            products.filter(company=selected_company)
            if selected_company
            else products.none()
        )

    categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True,
    )

    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Current filters without the page number, for pagination links.
    filter_params = request.GET.copy()
    filter_params.pop("page", None)
    for key in list(filter_params.keys()):
        if not filter_params.get(key):
            filter_params.pop(key)

    context = {
        "page_obj": page_obj,
        "categories": categories,
        "search_query": search_query,
        "selected_category": category_slug,
        "selected_category_obj": selected_category,
        "selected_company": selected_company,
        "filter_querystring": filter_params.urlencode(),
        "is_filtered": bool(search_query or category_slug or company_slug),
    }

    return render(request, "catalog/product_list.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.public()
        .select_related("category", "company")
        .prefetch_related("images"),
        slug=slug,
    )

    product_images = list(product.images.all())
    primary_image = product.primary_image

    context = {
        "product": product,
        "primary_image": primary_image,
        "gallery_images": [image for image in product_images if image != primary_image],
        "variants": product.variants.filter(is_active=True),
        "product_documents": product.documents.filter(is_public=True).order_by("title"),
        "related_products": (
            Product.objects.public()
            .filter(category=product.category)
            .exclude(pk=product.pk)
            .select_related("company")
            .prefetch_related("images")[:3]
        ),
    }

    return render(request, "catalog/product_detail.html", context)
