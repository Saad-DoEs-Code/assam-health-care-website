from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

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


def job_detail(request, slug):
    job = get_object_or_404(open_jobs(), slug=slug)

    if request.method == "POST":
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            if not form.is_spam():
                application = form.save(commit=False)
                application.job = job
                application.save()
            return redirect("job_application_success")
    else:
        form = JobApplicationForm()

    return render(request, "careers/job_detail.html", {"job": job, "form": form})


def job_application_success(request):
    return render(request, "careers/application_success.html")
