from django.urls import path

from .views import assistant_product_search, product_detail, product_list

urlpatterns = [
    path("products/", product_list, name="product_list"),
    path(
        "assistant/product-search/",
        assistant_product_search,
        name="assistant_product_search",
    ),
    path(
        "products/<slug:slug>/",
        product_detail,
        name="product_detail",
    ),
]
