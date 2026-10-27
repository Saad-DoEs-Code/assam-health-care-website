from django.db import models


# Create your models here.
class Inquiry(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("quoted", "Quoted"),
        ("converted", "Converted"),
        ("closed", "Closed"),
    ]

    name = models.CharField(max_length=150)

    organization = models.CharField(
        max_length=200,
        blank=True,
    )

    designation = models.CharField(
        max_length=150,
        blank=True,
    )

    phone = models.CharField(max_length=30)

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

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Inquiries"

    def __str__(self):
        return f"Inquiry #{self.pk} - {self.name}"


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
