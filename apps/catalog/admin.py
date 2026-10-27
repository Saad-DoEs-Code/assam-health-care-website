from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.utils.html import format_html

from .models import (
    Category,
    Product,
    ProductVariant,
    ProductImage,
    ProductDocument,
)


# Inline Classes
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("name", "description", "is_active", "display_order")


class ProductImageInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        primary_count = sum(
            1
            for form in self.forms
            if form.cleaned_data
            and form.cleaned_data.get("is_primary")
            and not form.cleaned_data.get("DELETE")
        )
        if primary_count > 1:
            raise ValidationError("Only one image can be marked as primary.")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    formset = ProductImageInlineFormSet
    extra = 1
    fields = ("preview", "image", "alt_text", "is_primary", "display_order")
    readonly_fields = ("preview",)

    @admin.display(description="Preview")
    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" alt="" style="max-height:60px;max-width:80px;">',
                obj.image.url,
            )
        return "—"


class ProductDocumentInline(admin.TabularInline):
    model = ProductDocument
    extra = 1
    fields = ("title", "file", "description", "is_public")


# Model Admin Classes
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "is_active", "display_order"]
    list_editable = ["is_active", "display_order"]
    list_filter = ["is_active", "parent"]
    list_select_related = ["parent"]
    search_fields = ["name", "description"]
    prepopulated_fields = {
        "slug": ("name",),
    }
    ordering = ["display_order", "name"]


class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "company",
        "category",
        "is_featured",
        "is_active",
        "display_order",
    )

    list_editable = (
        "is_featured",
        "is_active",
        "display_order",
    )

    list_filter = (
        "is_active",
        "is_featured",
        "category",
        "company",
    )

    list_select_related = ("company", "category")

    search_fields = (
        "name",
        "description",
        "short_description",
        "company__name",
    )

    prepopulated_fields = {
        "slug": ("name",),
    }

    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    ("category", "company"),
                    "short_description",
                    "description",
                ),
            },
        ),
        (
            "Visibility",
            {
                "description": (
                    "A product is shown on the website only when it, its "
                    "category, and its company are all active."
                ),
                "fields": (
                    ("is_active", "is_featured", "display_order"),
                    ("created_at", "updated_at"),
                ),
            },
        ),
    )

    ordering = (
        "display_order",
        "name",
    )

    inlines = [
        ProductVariantInline,
        ProductImageInline,
        ProductDocumentInline,
    ]


class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "product",
        "is_active",
        "display_order",
    )

    list_filter = (
        "is_active",
        "product",
    )

    list_select_related = ("product",)

    search_fields = (
        "name",
        "product__name",
    )

    ordering = (
        "product",
        "display_order",
        "name",
    )


class ProductDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "product",
        "is_public",
        "created_at",
    )

    list_filter = (
        "is_public",
    )

    list_select_related = ("product",)

    search_fields = (
        "title",
        "product__name",
    )


# Register your models here.
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductVariant, ProductVariantAdmin)
admin.site.register(ProductDocument, ProductDocumentAdmin)
