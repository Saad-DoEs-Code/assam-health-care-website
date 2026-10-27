from django.contrib import admin

from .models import City, Employee, Territory


@admin.register(Territory)
class TerritoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "display_order",
    )

    list_filter = ("is_active",)

    search_fields = ("name",)

    prepopulated_fields = {
        "slug": ("name",),
    }

    ordering = (
        "display_order",
        "name",
    )


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "territory",
        "is_active",
        "display_order",
    )

    list_filter = (
        "territory",
        "is_active",
    )

    list_editable = ("is_active", "display_order")

    list_select_related = ("territory",)

    search_fields = (
        "name",
        "territory__name",
    )

    ordering = (
        "territory",
        "display_order",
        "name",
    )


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "designation",
        "is_active",
        "display_on_website",
        "display_order",
    )

    list_editable = ("is_active", "display_on_website")

    list_filter = (
        "is_active",
        "display_on_website",
        "territories",
    )

    fieldsets = (
        (None, {"fields": ("name", "designation", "photo", "bio")}),
        (
            "Contact details",
            {
                "description": (
                    "Phone and email are shown publicly on the Sales Team page "
                    "when 'Display on website' is ticked."
                ),
                "fields": ("phone", "email"),
            },
        ),
        ("Coverage", {"fields": ("territories", "cities")}),
        (
            "Visibility",
            {"fields": (("is_active", "display_on_website", "display_order"),)},
        ),
    )

    search_fields = (
        "name",
        "designation",
        "phone",
        "email",
        "bio",
    )

    filter_horizontal = (
        "territories",
        "cities",
    )

    ordering = (
        "display_order",
        "name",
    )
