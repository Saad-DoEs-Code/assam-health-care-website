from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.core import ratelimit

from .forms import JobApplicationForm
from .models import Job


def open_jobs():
    """Published vacancies whose application deadline has not passed."""
    today = timezone.localdate()
    return Job.objects.filter(is_published=True).filter(
        Q(application_deadline__isnull=True) | Q(application_deadline__gte=today)
    )


def job_list(request):
    return render(request, "careers/job_list.html", {"jobs": open_jobs()})


RATE_LIMIT_MESSAGE = (
    "We have received several applications from your connection in a short "
    "time. Please try again in an hour."
)


@require_http_methods(["GET", "POST"])
def job_detail(request, slug):
    job = get_object_or_404(open_jobs(), slug=slug)
    rate_limited = False

    if request.method == "POST":
        form = JobApplicationForm(request.POST, request.FILES)
        rate_limited = ratelimit.is_limited(
            "job_application", request, ratelimit.JOB_APPLICATION_LIMIT
        )
        if rate_limited:
            form.is_valid()
            form.add_error(None, RATE_LIMIT_MESSAGE)
        elif form.is_valid():
            ratelimit.count_attempt(
                "job_application", request, ratelimit.JOB_APPLICATION_LIMIT
            )
            if not form.is_spam():
                application = form.save(commit=False)
                application.job = job
                application.save()
            return redirect("job_application_success")
    else:
        form = JobApplicationForm()

    return render(
        request,
        "careers/job_detail.html",
        {"job": job, "form": form, "rate_limited": rate_limited},
        status=429 if rate_limited else 200,
    )


def job_application_success(request):
    return render(request, "careers/application_success.html")
