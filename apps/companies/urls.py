from django.urls import path

from .views import partner_list

urlpatterns = [
    path("partners/", partner_list, name="partners"),
]
