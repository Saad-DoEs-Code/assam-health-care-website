
from django.urls import path

from .views import create_inquiry, inquiry_success


urlpatterns = [
    path("inquiry/", create_inquiry, name="create_inquiry"),
    path(
        "inquiry/success/",
        inquiry_success,
        name="inquiry_success",
    ),
]
