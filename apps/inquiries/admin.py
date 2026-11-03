from django import forms
from django.contrib import admin, messages
from django.db.models import Count
from django.utils import timezone
from django.utils.html import format_html, format_html_join

from .models import Inquiry, InquiryItem, WatchlistEntry
from .screening import mark_as_competitor, screen_inquiry

RISK_BADGE_STYLES = {
    Inquiry.RISK_LOW: ("#17694a", "#ecf7f1"),
    Inquiry.RISK_MEDIUM: ("#8a5300", "#fff4e0"),
    Inquiry.RISK_HIGH: ("#a3251a", "#fdf2f1"),
}


class InquiryItemInline(admin.TabularInline):
    model = InquiryItem
    extra = 0
    fields = ("product", "variant", "quantity", "notes")
    autocomplete_fields = ("product",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "product", "variant"
        )


class InquiryAdminForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        is_verified = cleaned_data.get("is_verified")

        if status in Inquiry.PRICED_STATUSES and not is_verified:
            self.add_error(
                "status",
                "Verify the requester (tick “Is verified” and add a note) "
                "before marking the inquiry as quoted or converted.",
            )

        if is_verified and not cleaned_data.get("verification_note"):
            self.add_error(
                "verification_note",
                "Note how the requester was verified, e.g. callback to the hospital landline.",
            )

        if is_verified and cleaned_data.get("is_suspected_competitor"):
            self.add_error(
                "is_verified",
                "An inquiry marked as a suspected competitor cannot be verified.",
            )

        return cleaned_data


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    form = InquiryAdminForm

    list_display = (
        "id",
        "name",
        "organization",
        "organization_type",
        "city",
        "item_count",
        "risk_badge",
        "is_verified",
        "status",
        "assigned_employee",
        "created_at",
    )

    list_display_links = ("id", "name")

    list_filter = (
        "risk_level",
        "is_verified",
        "status",
        "is_suspected_competitor",
        "is_returning_customer",
        "organization_type",
        "city__territory",
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
        "risk_summary",
        "is_returning_customer",
        "verified_by",
        "verified_at",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Customer",
            {
                "fields": (
                    ("name", "designation"),
                    ("organization", "organization_type"),
                    ("phone", "whatsapp"),
                    "email",
                    "city",
                    "message",
                ),
            },
        ),
        (
            "Screening",
            {
                "description": (
                    "Automatic risk check. Verify every requester before sending "
                    "prices: call back on a known landline, or ask for a request "
                    "on hospital letterhead. Quote only the items requested."
                ),
                "fields": (
                    "risk_summary",
                    "is_returning_customer",
                    ("is_verified", "verification_note"),
                    ("verified_by", "verified_at"),
                    "is_suspected_competitor",
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

    actions = [
        "mark_verification_pending",
        "mark_as_suspected_competitor",
        "rerun_risk_check",
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _item_count=Count("items", distinct=True)
        )

    @admin.display(description="Products", ordering="_item_count")
    def item_count(self, obj):
        return obj._item_count

    @admin.display(description="Risk", ordering="risk_level")
    def risk_badge(self, obj):
        colour, background = RISK_BADGE_STYLES[obj.risk_level]
        label = obj.get_risk_level_display()
        if obj.is_suspected_competitor:
            label = "Competitor"
        return format_html(
            '<span style="padding:2px 8px;border-radius:999px;font-weight:600;'
            'color:{};background:{}" title="{}">{}</span>',
            colour,
            background,
            "; ".join(obj.risk_reason_list),
            label,
        )

    @admin.display(description="Risk check")
    def risk_summary(self, obj):
        if not obj.pk:
            return "—"
        reasons = obj.risk_reason_list or ["No warning signs found."]
        return format_html(
            "{}<ul style='margin:6px 0 0 18px;padding:0'>{}</ul>",
            self.risk_badge(obj),
            format_html_join("", "<li>{}</li>", ((reason,) for reason in reasons)),
        )

    def save_model(self, request, obj, form, change):
        # Record who verified the inquiry, and when.
        if obj.is_verified and not obj.verified_at:
            obj.verified_by = request.user
            obj.verified_at = timezone.now()
        elif not obj.is_verified:
            obj.verified_by = None
            obj.verified_at = None
        super().save_model(request, obj, form, change)

    @admin.action(description="Set status to “Verification pending”")
    def mark_verification_pending(self, request, queryset):
        updated = queryset.exclude(status__in=Inquiry.PRICED_STATUSES).update(
            status="verification_pending"
        )
        self.message_user(request, f"{updated} inquiry(ies) set to verification pending.")

    @admin.action(description="Mark as suspected competitor (close and add to watchlist)")
    def mark_as_suspected_competitor(self, request, queryset):
        inquiries = list(queryset)
        added = sum(mark_as_competitor(inquiry, request.user) for inquiry in inquiries)
        self.message_user(
            request,
            f"{len(inquiries)} inquiry(ies) closed as suspected competitor; "
            f"{added} new watchlist entr{'y' if added == 1 else 'ies'} added.",
            messages.WARNING,
        )

    @admin.action(description="Re-run risk check")
    def rerun_risk_check(self, request, queryset):
        inquiries = list(queryset)
        for inquiry in inquiries:
            screen_inquiry(inquiry)
        self.message_user(request, f"Risk check re-run for {len(inquiries)} inquiry(ies).")


@admin.register(WatchlistEntry)
class WatchlistEntryAdmin(admin.ModelAdmin):
    # New inquiries matching an active entry are flagged as high risk.
    list_display = ("value", "kind", "reason", "is_active", "source_inquiry", "created_at")
    list_filter = ("kind", "is_active")
    search_fields = ("value", "normalized_value", "reason")
    list_editable = ("is_active",)
    readonly_fields = ("normalized_value", "source_inquiry", "created_by", "created_at")
    fields = (
        "kind",
        "value",
        "normalized_value",
        "reason",
        "is_active",
        "source_inquiry",
        "created_by",
        "created_at",
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
