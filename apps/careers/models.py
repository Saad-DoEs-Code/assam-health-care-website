from django.db import models
from django.urls import reverse


class Job(models.Model):
    title = models.CharField(max_length=200)

    slug = models.SlugField(unique=True)

    department = models.CharField(
        max_length=150,
        blank=True,
    )

    location = models.CharField(
        max_length=150,
        blank=True,
    )

    employment_type = models.CharField(
        max_length=100,
        blank=True,
    )

    description = models.TextField()

    requirements = models.TextField(
        blank=True,
    )

    responsibilities = models.TextField(
        blank=True,
    )

    is_published = models.BooleanField(default=False)

    application_deadline = models.DateField(
        blank=True,
        null=True,
    )

    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("job_detail", kwargs={"slug": self.slug})


class JobApplication(models.Model):
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications",
    )

    name = models.CharField(max_length=150)

    email = models.EmailField()

    phone = models.CharField(max_length=30)

    city = models.CharField(
        max_length=150,
        blank=True,
    )

    cover_letter = models.TextField(
        blank=True,
    )

    resume = models.FileField(
        upload_to="careers/resumes/",
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.job.title}"
