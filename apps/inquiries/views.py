import uuid

from django.db import transaction
from django.shortcuts import redirect, render

from apps.catalog.models import Category
from apps.inquiries.forms import (
    MAX_INQUIRY_ITEMS,
    InquiryForm,
    InquiryItemFormSet,
    get_quote_catalogue,
)
from apps.inquiries.models import Inquiry, InquiryItem

ITEM_FORMSET_PREFIX = "items"

# Session keys
SUBMITTED_TOKENS_KEY = "inquiry_submitted_tokens"
LAST_INQUIRY_KEY = "last_inquiry_id"


def _get_preselected_product(request, catalogue):
    """
    Return the public product named by ?product=<id>, or None.

    Malformed, unknown, and inactive ids are ignored instead of raising an
    error, so an outdated link still opens a working quotation form.
    """
    raw_product_id = request.GET.get("product", "")
    if not raw_product_id.isdigit():
        return None
    product_id = int(raw_product_id)
    for product in catalogue:
        if product.pk == product_id:
            return product
    return None


def _catalogue_for_script(catalogue):
    """Only the fields the product picker needs; no internal data."""
    return [
        {
            "id": product.pk,
            "name": product.name,
            "category": product.category.slug,
            "company": product.company.name,
            "variants": [
                {"id": variant.pk, "name": variant.name}
                for variant in product.active_variants
            ],
        }
        for product in catalogue
    ]


def create_inquiry(request):
    catalogue = get_quote_catalogue()
    formset_kwargs = {
        "prefix": ITEM_FORMSET_PREFIX,
        "form_kwargs": {"catalogue": catalogue},
    }

    if request.method == "POST":
        form = InquiryForm(request.POST)
        item_formset = InquiryItemFormSet(request.POST, **formset_kwargs)
        submission_token = request.POST.get("submission_token", "")

        # A double-click or browser resubmission of a request that was
        # already saved: show the confirmation again instead of saving twice.
        if submission_token and submission_token in request.session.get(
            SUBMITTED_TOKENS_KEY, []
        ):
            return redirect("inquiry_success")

        if form.is_valid() and item_formset.is_valid():
            items = item_formset.selected_items()

            if form.is_spam():
                return redirect("inquiry_success")

            if not items and not form.cleaned_data.get("message"):
                form.add_error(
                    None,
                    "Please add at least one product, or describe your "
                    "requirements in the message field.",
                )
            else:
                with transaction.atomic():
                    inquiry = form.save()
                    InquiryItem.objects.bulk_create(
                        [
                            InquiryItem(
                                inquiry=inquiry,
                                product=item["product"],
                                variant=item.get("variant"),
                                quantity=item["quantity"],
                                notes=item.get("notes", ""),
                            )
                            for item in items
                        ]
                    )

                if submission_token:
                    tokens = request.session.get(SUBMITTED_TOKENS_KEY, [])
                    request.session[SUBMITTED_TOKENS_KEY] = (tokens + [submission_token])[-10:]
                request.session[LAST_INQUIRY_KEY] = inquiry.pk

                return redirect("inquiry_success")
    else:
        form = InquiryForm()
        preselected_product = _get_preselected_product(request, catalogue)
        initial_items = (
            [{"product": preselected_product.pk, "quantity": 1}]
            if preselected_product
            else []
        )
        item_formset = InquiryItemFormSet(initial=initial_items, **formset_kwargs)
        submission_token = ""

    context = {
        "form": form,
        "item_formset": item_formset,
        "submission_token": submission_token or uuid.uuid4().hex,
        "catalogue_data": _catalogue_for_script(catalogue),
        "quote_categories": Category.objects.filter(
            is_active=True,
            products__in=[product.pk for product in catalogue],
        ).distinct(),
        "has_cities": form.fields["city"].queryset.exists(),
        "max_items": MAX_INQUIRY_ITEMS,
    }

    return render(request, "inquiries/inquiry_form.html", context)


def inquiry_success(request):
    inquiry = None
    inquiry_id = request.session.get(LAST_INQUIRY_KEY)

    if inquiry_id:
        # Only the visitor who submitted the inquiry has its id in their
        # session, so the summary is never shown to anyone else.
        inquiry = (
            Inquiry.objects.filter(pk=inquiry_id)
            .prefetch_related("items__product", "items__variant")
            .first()
        )

    return render(request, "inquiries/inquiry_success.html", {"inquiry": inquiry})
