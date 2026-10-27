from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse

MAX_LEADERSHIP_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_photo_size(photo):
    if photo and photo.size > MAX_LEADERSHIP_PHOTO_SIZE:
        raise ValidationError("The photo must be 5 MB or smaller.")


class Page(models.Model):
    title = models.CharField(max_length=200)

    slug = models.SlugField(unique=True)

    content = models.TextField(blank=True)

    meta_title = models.CharField(
        max_length=200,
        blank=True,
    )

    meta_description = models.CharField(
        max_length=300,
        blank=True,
    )

    is_published = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        if self.slug == "about":
            return reverse("about")
        return reverse("page_detail", kwargs={"slug": self.slug})


class SiteSettings(models.Model):
    company_name = models.CharField(max_length=200)

    tagline = models.CharField(
        max_length=300,
        blank=True,
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    whatsapp = models.CharField(
        max_length=30,
        blank=True,
    )

    logo = models.ImageField(
        upload_to="site/",
        blank=True,
        null=True,
    )

    favicon = models.ImageField(
        upload_to="site/",
        blank=True,
        null=True,
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.company_name


class LeadershipMessage(models.Model):
    """
    A message from the company's leadership (for example the CEO), shown on
    the homepage and the About page only while it is published.
    """

    name = models.CharField(max_length=150)

    designation = models.CharField(
        max_length=150,
        help_text="Exact title, for example Chief Executive Officer.",
    )

    photo = models.ImageField(
        upload_to="leadership/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_photo_size,
        ],
        help_text=(
            "Head-and-shoulders photo, at least 800 × 800 pixels. "
            "JPG, PNG or WebP, up to 5 MB."
        ),
    )

    message = models.TextField(
        help_text="The full message. Separate paragraphs with a blank line.",
    )

    excerpt = models.CharField(
        max_length=300,
        blank=True,
        help_text=(
            "Short quote for the homepage. Leave blank to use the start of "
            "the message."
        ),
    )

    is_published = models.BooleanField(
        default=False,
        help_text="Only a published message appears on the website.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.name} — {self.designation}"

    @classmethod
    def get_published(cls):
        """The most recently updated published message, or None."""
        return cls.objects.filter(is_published=True).first()
