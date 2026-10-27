from django.db import models


# Create your models here.
class Territory(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)

    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "display_order",
            "name",
        ]
        verbose_name_plural = "Territories"

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=150)

    territory = models.ForeignKey(
        Territory,
        on_delete=models.PROTECT,
        related_name="cities",
    )

    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name_plural = "Cities"

    def __str__(self):
        return self.name


class Employee(models.Model):
    name = models.CharField(max_length=200)
    designation = models.CharField(max_length=150)

    phone = models.CharField(max_length=11)
    email = models.EmailField(blank=True)

    photo = models.ImageField(
        upload_to="team/photos/",
        blank=True,
        null=True,
    )
    bio = models.TextField(blank=True)

    territories = models.ManyToManyField(
        Territory,
        related_name="employees",
        blank=True,
    )

    cities = models.ManyToManyField(
        City,
        related_name="employees",
        blank=True,
    )

    is_active = models.BooleanField(default=True)
    display_on_website = models.BooleanField(default=True)

    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "display_order",
            "name",
        ]

    def __str__(self):
        return self.name
