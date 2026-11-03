from django.contrib import admin
from django.utils.html import format_html

from .models import AssistantAnswer, LeadershipMessage, Page, SiteSettings


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


@admin.register(LeadershipMessage)
class LeadershipMessageAdmin(admin.ModelAdmin):
    # The website shows the most recently updated published message.
    list_display = (
        "name",
        "designation",
        "is_published",
        "updated_at",
    )

    list_filter = ("is_published",)

    search_fields = (
        "name",
        "designation",
        "message",
    )

    readonly_fields = (
        "photo_preview",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (None, {"fields": ("name", "designation", ("photo", "photo_preview"))}),
        ("Message", {"fields": ("message", "excerpt")}),
        (
            "Visibility",
            {
                "description": (
                    "Nothing is shown on the website until this is published. "
                    "If several messages are published, the most recently "
                    "updated one is shown."
                ),
                "fields": ("is_published", ("created_at", "updated_at")),
            },
        ),
    )

    @admin.display(description="Preview")
    def photo_preview(self, obj):
        if obj.pk and obj.photo:
            return format_html(
                '<img src="{}" alt="" style="max-height:120px;border-radius:8px;">',
                obj.photo.url,
            )
        return "—"


@admin.register(AssistantAnswer)
class AssistantAnswerAdmin(admin.ModelAdmin):
    # Common questions offered by the help assistant on every page. The
    # assistant also has built-in options (product search, quote, contact).
    list_display = (
        "question",
        "display_order",
        "is_published",
        "updated_at",
    )

    list_editable = ("display_order", "is_published")

    list_filter = ("is_published",)

    search_fields = ("question", "answer")

    fieldsets = (
        (None, {"fields": ("question", "answer")}),
        (
            "Button under the answer (optional)",
            {"fields": ("link_label", "link_url")},
        ),
        (
            "Visibility",
            {
                "description": (
                    "Questions are listed in display order. The assistant "
                    "never shows prices; keep answers free of them."
                ),
                "fields": ("display_order", "is_published"),
            },
        ),
    )
