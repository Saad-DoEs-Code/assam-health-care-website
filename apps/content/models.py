from django.db import models
from django.urls import reverse


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
