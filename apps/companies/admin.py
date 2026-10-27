from django.contrib import admin
from .models import Company


class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "is_official_partner", "is_active", "created_at")
    list_editable = ("is_official_partner", "is_active")
    list_filter = ("is_official_partner", "is_active")
    search_fields = ("name", "description")
    prepopulated_fields = {
        "slug": ("name",),
    }
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("name", "slug", "description", "website", "logo")}),
        (
            "Status",
            {
                "description": (
                    "Only mark a company as an official partner when a formal "
                    "distribution agreement exists. This label is shown publicly."
                ),
                "fields": (
                    ("is_official_partner", "is_active"),
                    ("created_at", "updated_at"),
                ),
            },
        ),
    )


admin.site.register(Company, CompanyAdmin)
