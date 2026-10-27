from django.contrib import admin
from django.db.models import Count

from .models import Inquiry, InquiryItem


class InquiryItemInline(admin.TabularInline):
    model = InquiryItem
    extra = 0
    fields = ("product", "variant", "quantity", "notes")
    autocomplete_fields = ("product",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "product", "variant"
        )


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "organization",
        "phone",
        "city",
        "item_count",
        "status",
        "assigned_employee",
        "created_at",
    )

    list_display_links = ("id", "name")

    list_filter = (
        "status",
        "city__territory",
        "city",
        "assigned_employee",
        "created_at",
    )

    list_select_related = ("city", "assigned_employee")

    search_fields = (
        "name",
        "organization",
        "phone",
        "whatsapp",
        "email",
        "message",
        "items__product__name",
    )

    date_hierarchy = "created_at"

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Customer",
            {
                "fields": (
                    ("name", "designation"),
                    "organization",
                    ("phone", "whatsapp"),
                    "email",
                    "city",
                    "message",
                ),
            },
        ),
        (
            "Follow-up",
            {
                "fields": (
                    ("status", "assigned_employee"),
                    ("created_at", "updated_at"),
                ),
            },
        ),
    )

    ordering = ("-created_at",)

    inlines = [
        InquiryItemInline,
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _item_count=Count("items", distinct=True)
        )

    @admin.display(description="Products", ordering="_item_count")
    def item_count(self, obj):
        return obj._item_count
