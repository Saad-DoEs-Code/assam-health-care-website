from django.contrib import admin
from django.db.models import Count

from .models import Job, JobApplication


class JobApplicationInline(admin.TabularInline):
    model = JobApplication
    extra = 0
    fields = ("name", "email", "phone", "city", "resume", "created_at")
    readonly_fields = ("name", "email", "phone", "city", "resume", "created_at")
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        # Applications come from the public website, not from staff.
        return False


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "department",
        "location",
        "employment_type",
        "is_published",
        "application_deadline",
        "application_count",
        "created_at",
    )

    list_filter = (
        "is_published",
        "department",
        "employment_type",
        "location",
    )

    search_fields = (
        "title",
        "department",
        "location",
        "description",
        "requirements",
    )

    prepopulated_fields = {
        "slug": ("title",),
    }

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "display_order",
        "-created_at",
    )

    inlines = [
        JobApplicationInline,
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _application_count=Count("applications")
        )

    @admin.display(description="Applications", ordering="_application_count")
    def application_count(self, obj):
        return obj._application_count


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "job",
        "email",
        "phone",
        "city",
        "created_at",
    )

    list_filter = (
        "job",
        "created_at",
    )

    list_select_related = ("job",)

    search_fields = (
        "name",
        "email",
        "phone",
        "city",
        "cover_letter",
    )

    readonly_fields = ("created_at",)

    date_hierarchy = "created_at"

    ordering = ("-created_at",)
