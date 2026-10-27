from django.urls import path

from .views import job_application_success, job_detail, job_list

urlpatterns = [
    path("careers/", job_list, name="job_list"),
    path(
        "careers/application-received/",
        job_application_success,
        name="job_application_success",
    ),
    path("careers/<slug:slug>/", job_detail, name="job_detail"),
]
