import re

from django import forms
from django.db.models import Prefetch

from apps.catalog.models import Product, ProductVariant
from apps.inquiries.models import Inquiry

# Upper limits that keep a single request a sensible size.
MAX_INQUIRY_ITEMS = 50
MAX_ITEM_QUANTITY = 1_000_000

# Number of blank product rows rendered for visitors without JavaScript.
# The JavaScript product picker removes them and adds rows on demand instead.
FALLBACK_BLANK_ROWS = 3

PHONE_PATTERN = re.compile(r"^\+?[\d\s\-()]+$")


def validate_phone_number(value):
    digits = re.sub(r"\D", "", value)
    if not PHONE_PATTERN.match(value) or not 10 <= len(digits) <= 15:
        raise forms.ValidationError(
            "Enter a valid phone number, for example 0300-1234567."
        )
    return value


def get_quote_catalogue():
    """
    Return every publicly visible product with its active variants.

    Loaded once per request and shared by all item rows, the product picker
    and the no-JavaScript fallback, so the number of queries does not grow
    with the number of rows.
    """
    return list(
        Product.objects.public()
        .select_related("category", "company")
        .prefetch_related(
            Prefetch(
                "variants",
                queryset=ProductVariant.objects.filter(is_active=True),
                to_attr="active_variants",
            )
        )
        .order_by(
            "category__display_order",
            "category__name",
            "display_order",
            "name",
        )
    )


class HoneypotMixin(forms.Form):
    """
    A hidden field that real visitors leave empty. Simple bots fill in every
    field, which lets the view discard their submissions quietly.
    """

    website = forms.CharField(
        required=False,
        label="Leave this field empty",
        widget=forms.TextInput(
            attrs={"autocomplete": "off", "tabindex": "-1"}
        ),
    )

    def is_spam(self):
        return bool(self.cleaned_data.get("website"))


class InquiryForm(HoneypotMixin, forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = [
            "name",
            "organization",
            "designation",
            "phone",
            "whatsapp",
            "email",
            "city",
            "message",
        ]

        labels = {
            "name": "Full name",
            "organization": "Hospital / organization",
            "whatsapp": "WhatsApp number",
            "message": "Message or additional requirements",
        }

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Your full name",
                    "autocomplete": "name",
                }
            ),
            "organization": forms.TextInput(
                attrs={
                    "placeholder": "Hospital, clinic, or organization",
                    "autocomplete": "organization",
                }
            ),
            "designation": forms.TextInput(
                attrs={
                    "placeholder": "Your job title",
                    "autocomplete": "organization-title",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "placeholder": "e.g. 0300-1234567",
                    "type": "tel",
                    "autocomplete": "tel",
                }
            ),
            "whatsapp": forms.TextInput(
                attrs={
                    "placeholder": "If different from your phone number",
                    "type": "tel",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "you@example.com",
                    "autocomplete": "email",
                }
            ),
            "city": forms.Select(),
            "message": forms.Textarea(
                attrs={
                    "placeholder": (
                        "Delivery timelines, specifications, or any other "
                        "details that help us prepare your quotation."
                    ),
                    "rows": 5,
                    "maxlength": 3000,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["city"].queryset = (
            self.fields["city"]
            .queryset.filter(is_active=True, territory__is_active=True)
            .order_by("display_order", "name")
        )

        self.fields["city"].empty_label = "Select your city"

        self.fields["organization"].required = False
        self.fields["designation"].required = False
        self.fields["whatsapp"].required = False
        self.fields["email"].required = False

        self.fields["message"].max_length = 3000

    def clean_phone(self):
        return validate_phone_number(self.cleaned_data["phone"].strip())

    def clean_whatsapp(self):
        whatsapp = self.cleaned_data.get("whatsapp", "").strip()
        if whatsapp:
            validate_phone_number(whatsapp)
        return whatsapp

    def clean_message(self):
        message = self.cleaned_data.get("message", "")
        if len(message) > 3000:
            raise forms.ValidationError(
                "Please keep your message under 3,000 characters."
            )
        return message


class InquiryItemForm(forms.Form):
    """
    One requested product. The product and variant are always re-checked
    against the database, so a forged or stale identifier cannot be saved.
    """

    product = forms.ModelChoiceField(
        queryset=Product.objects.public(),
        error_messages={
            "invalid_choice": (
                "This product is not available. Please remove it and "
                "choose another product."
            ),
        },
    )

    variant = forms.ModelChoiceField(
        queryset=ProductVariant.objects.filter(is_active=True),
        required=False,
        label="Size / variant",
        error_messages={
            "invalid_choice": "Select one of the available variants.",
        },
    )

    quantity = forms.IntegerField(
        min_value=1,
        max_value=MAX_ITEM_QUANTITY,
        initial=1,
        widget=forms.NumberInput(attrs={"inputmode": "numeric"}),
    )

    notes = forms.CharField(
        max_length=300,
        required=False,
        label="Notes (optional)",
        widget=forms.TextInput(
            attrs={"placeholder": "e.g. packaging, brand preference"}
        ),
    )

    def __init__(self, *args, catalogue=None, **kwargs):
        super().__init__(*args, **kwargs)

        catalogue = catalogue or []
        products_by_id = {product.pk: product for product in catalogue}

        # The product chosen in this row (from submitted data or the
        # preselected initial value), if it is a public product.
        self.selected_product = products_by_id.get(
            self._get_raw_product_id()
        )

        self.fields["product"].choices = self._grouped_product_choices(catalogue)

        if self.selected_product:
            variants = self.selected_product.active_variants
            self.fields["variant"].choices = [("", "Any / not sure")] + [
                (variant.pk, variant.name) for variant in variants
            ]
        else:
            self.fields["variant"].choices = [("", "Any / not sure")] + [
                (
                    product.name,
                    [(variant.pk, variant.name) for variant in product.active_variants],
                )
                for product in catalogue
                if product.active_variants
            ]

    def has_changed(self):
        """
        A row counts as filled in when it names a product, variant or note.

        Quantity alone is ignored: blank rows show a default of 1, and rows
        removed by JavaScript send no quantity at all. Treating both as empty
        lets Django skip them instead of reporting errors.
        """
        if not self.is_bound:
            return super().has_changed()
        return any(
            str(self.data.get(self.add_prefix(name), "")).strip()
            for name in ("product", "variant", "notes")
        )

    @property
    def has_variants(self):
        return bool(self.selected_product and self.selected_product.active_variants)

    def _get_raw_product_id(self):
        if self.is_bound:
            raw_value = self.data.get(self.add_prefix("product"))
        else:
            raw_value = self.initial.get("product")
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _grouped_product_choices(catalogue):
        groups = {}
        for product in catalogue:
            groups.setdefault(product.category.name, []).append(
                (product.pk, f"{product.name} ({product.company.name})")
            )
        return [("", "Select a product")] + list(groups.items())

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        variant = cleaned_data.get("variant")

        if product and variant and variant.product_id != product.pk:
            self.add_error(
                "variant",
                "This variant does not belong to the selected product.",
            )

        return cleaned_data


class BaseInquiryItemFormSet(forms.BaseFormSet):
    def clean(self):
        super().clean()

        if any(self.errors):
            return

        seen = set()
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            product = form.cleaned_data.get("product")
            if not product:
                continue
            variant = form.cleaned_data.get("variant")
            key = (product.pk, variant.pk if variant else None)
            if key in seen:
                label = f"{product.name} ({variant.name})" if variant else product.name
                raise forms.ValidationError(
                    f"{label} is listed more than once. Combine the quantities "
                    "into a single row, or choose a different variant."
                )
            seen.add(key)

        if len(seen) > MAX_INQUIRY_ITEMS:
            raise forms.ValidationError(
                f"A single request can include up to {MAX_INQUIRY_ITEMS} "
                "products. Please send the rest in a second request."
            )

    def selected_items(self):
        """Cleaned data for every non-blank, non-deleted row."""
        return [
            form.cleaned_data
            for form in self.forms
            if form.cleaned_data
            and form.cleaned_data.get("product")
            and not (self.can_delete and self._should_delete_form(form))
        ]


InquiryItemFormSet = forms.formset_factory(
    InquiryItemForm,
    formset=BaseInquiryItemFormSet,
    extra=FALLBACK_BLANK_ROWS,
    can_delete=True,
    # The item limit is checked in BaseInquiryItemFormSet.clean() because
    # Django's validate_max would also count the blank fallback rows.
    max_num=MAX_INQUIRY_ITEMS + FALLBACK_BLANK_ROWS,
    # Bounds how many rows Django will build from a (possibly forged)
    # TOTAL_FORMS value.
    absolute_max=MAX_INQUIRY_ITEMS + FALLBACK_BLANK_ROWS,
)
