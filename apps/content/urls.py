from django.urls import path

from . import views

urlpatterns = [
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("pages/<slug:slug>/", views.page_detail, name="page_detail"),
]
