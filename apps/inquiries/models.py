from django.conf import settings
from django.db import models


class Inquiry(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("verification_pending", "Verification pending"),
        ("quoted", "Quoted"),
        ("converted", "Converted"),
        ("closed", "Closed"),
    ]

    # Statuses that mean prices have been (or are being) shared. An inquiry
    # must be verified before it can move into one of these.
    PRICED_STATUSES = ("quoted", "converted")

    ORGANIZATION_TYPE_CHOICES = [
        ("hospital", "Hospital"),
        ("clinic", "Clinic"),
        ("dialysis_centre", "Dialysis centre"),
        ("laboratory", "Laboratory"),
        ("pharmacy", "Pharmacy"),
        ("distributor", "Distributor / trader"),
        ("other", "Other"),
    ]

    RISK_LOW = "low"
    RISK_MEDIUM = "medium"
    RISK_HIGH = "high"
    RISK_CHOICES = [
        (RISK_LOW, "Low"),
        (RISK_MEDIUM, "Medium"),
        (RISK_HIGH, "High"),
    ]

    name = models.CharField(max_length=150)

    organization_type = models.CharField(
        max_length=30,
        choices=ORGANIZATION_TYPE_CHOICES,
        blank=True,
    )

    organization = models.CharField(
        max_length=200,
        blank=True,
    )

    designation = models.CharField(
        max_length=150,
        blank=True,
    )

    phone = models.CharField(max_length=30)

    # Phone in +92 format, set on save, so the same number is recognised
    # across inquiries whatever format it was typed in.
    phone_normalized = models.CharField(
        max_length=20,
        blank=True,
        editable=False,
        db_index=True,
    )

    whatsapp = models.CharField(
        max_length=30,
        blank=True,
    )

    email = models.EmailField(blank=True)

    city = models.ForeignKey(
        "team.City",
        on_delete=models.PROTECT,
        related_name="inquiries",
    )

    message = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
    )

    assigned_employee = models.ForeignKey(
        "team.Employee",
        on_delete=models.SET_NULL,
        related_name="assigned_inquiries",
        blank=True,
        null=True,
    )

    # --- Screening (filled in automatically; see apps/inquiries/screening.py)

    risk_level = models.CharField(
        max_length=10,
        choices=RISK_CHOICES,
        default=RISK_LOW,
    )

    risk_reasons = models.TextField(
        blank=True,
        help_text="One reason per line, written by the automatic check.",
    )

    is_returning_customer = models.BooleanField(
        default=False,
        help_text="Matches an earlier inquiry that was converted.",
    )

    # --- Verification by the sales team before prices are shared

    is_verified = models.BooleanField(
        default=False,
        help_text="Tick after confirming the person and organisation are genuine.",
    )

    verification_note = models.CharField(
        max_length=300,
        blank=True,
        help_text="How it was verified, e.g. callback to the hospital landline.",
    )

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="verified_inquiries",
        blank=True,
        null=True,
    )

    verified_at = models.DateTimeField(blank=True, null=True)

    is_suspected_competitor = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Inquiries"

    def __str__(self):
        return f"Inquiry #{self.pk} - {self.name}"

    def save(self, *args, **kwargs):
        from apps.inquiries.screening import normalize_phone

        self.phone_normalized = normalize_phone(self.phone)
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "phone" in update_fields:
            kwargs["update_fields"] = set(update_fields) | {"phone_normalized"}
        super().save(*args, **kwargs)

    @property
    def risk_reason_list(self):
        return [line for line in self.risk_reasons.splitlines() if line.strip()]


class InquiryItem(models.Model):
    inquiry = models.ForeignKey(
        Inquiry,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="inquiry_items",
    )

    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        related_name="inquiry_items",
        blank=True,
        null=True,
    )

    quantity = models.PositiveIntegerField(
        blank=True,
        null=True,
    )

    notes = models.CharField(
        max_length=300,
        blank=True,
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.product.name} - Inquiry #{self.inquiry.pk}"


class WatchlistEntry(models.Model):
    """
    Identifiers of known competitors or other contacts who should not
    receive price quotations. New inquiries matching an active entry are
    flagged as high risk.
    """

    KIND_PHONE = "phone"
    KIND_EMAIL = "email"
    KIND_EMAIL_DOMAIN = "email_domain"
    KIND_ORGANIZATION = "organization"
    KIND_KEYWORD = "keyword"
    KIND_CHOICES = [
        (KIND_PHONE, "Phone number"),
        (KIND_EMAIL, "Email address"),
        (KIND_EMAIL_DOMAIN, "Email domain"),
        (KIND_ORGANIZATION, "Organisation name"),
        (KIND_KEYWORD, "Keyword"),
    ]

    kind = models.CharField(max_length=20, choices=KIND_CHOICES)

    value = models.CharField(
        max_length=200,
        help_text=(
            "Phone numbers can be in any format. For organisation names and "
            "keywords, any inquiry containing this text is flagged."
        ),
    )

    normalized_value = models.CharField(max_length=200, editable=False, db_index=True)

    reason = models.CharField(max_length=300, blank=True)

    is_active = models.BooleanField(default=True)

    source_inquiry = models.ForeignKey(
        Inquiry,
        on_delete=models.SET_NULL,
        related_name="watchlist_entries",
        blank=True,
        null=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="+",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["kind", "value"]
        verbose_name = "Watchlist entry"
        verbose_name_plural = "Watchlist"
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "normalized_value"],
                name="unique_watchlist_entry",
            ),
        ]

    def __str__(self):
        return f"{self.get_kind_display()}: {self.value}"

    def save(self, *args, **kwargs):
        from apps.inquiries.screening import normalize_identifier

        self.normalized_value = normalize_identifier(self.kind, self.value)
        super().save(*args, **kwargs)
