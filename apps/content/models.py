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


def validate_assistant_link(url):
    """Links must stay on this site ("/products/") or use HTTPS."""
    if url and not (
        (url.startswith("/") and not url.startswith("//"))
        or url.startswith("https://")
    ):
        raise ValidationError(
            'Enter a page on this site starting with "/" (for example '
            '/products/) or a full address starting with https://.'
        )


class AssistantAnswer(models.Model):
    """
    A ready-made answer in the website's help assistant (the chat button in
    the corner of every page). Visitors pick a question; nothing is typed
    freely, so the assistant only ever says what staff have written here.
    """

    question = models.CharField(
        max_length=120,
        help_text="Shown as a button, for example: Do you deliver outside Multan?",
    )

    answer = models.TextField(
        help_text=(
            "Plain text. Separate paragraphs with a blank line. Do not "
            "include prices: price questions should go to the quote form."
        ),
    )

    link_label = models.CharField(
        max_length=60,
        blank=True,
        help_text="Optional button under the answer, for example: See our cities.",
    )

    link_url = models.CharField(
        max_length=300,
        blank=True,
        validators=[validate_assistant_link],
        help_text="Page for that button, for example /team/ or /products/.",
    )

    display_order = models.PositiveIntegerField(default=0)

    is_published = models.BooleanField(
        default=True,
        help_text="Only published answers appear in the assistant.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "question"]

    def __str__(self):
        return self.question

    def clean(self):
        super().clean()
        if bool(self.link_label) != bool(self.link_url):
            raise ValidationError(
                "Fill in both the button label and its page, or leave both empty."
            )
