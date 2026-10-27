from django.contrib import admin

from .models import Page, SiteSettings


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    # A page with the slug "about" replaces the default About page text.
    # Other published pages are available at /pages/<slug>/.
    list_display = (
        "title",
        "slug",
        "is_published",
        "updated_at",
    )

    list_filter = ("is_published",)

    search_fields = (
        "title",
        "content",
        "meta_title",
        "meta_description",
    )

    prepopulated_fields = {
        "slug": ("title",),
    }

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("title",)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "tagline",
        "phone",
        "updated_at",
    )

    readonly_fields = ("updated_at",)

    fieldsets = (
        (None, {"fields": ("company_name", "tagline", "logo", "favicon")}),
        (
            "Contact details",
            {
                "description": (
                    "Shown in the website header, footer and contact page. "
                    "Email and WhatsApp are only displayed when filled in."
                ),
                "fields": ("phone", "whatsapp", "email", "address"),
            },
        ),
        (None, {"fields": ("updated_at",)}),
    )

    def has_add_permission(self, request):
        # The website reads the first record only, so keep a single one.
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
