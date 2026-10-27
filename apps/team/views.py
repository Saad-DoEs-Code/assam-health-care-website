from django.db.models import Prefetch
from django.shortcuts import render

from .models import City, Employee, Territory


def public_employees():
    """Employees that are active and approved for display on the website."""
    return Employee.objects.filter(is_active=True, display_on_website=True)


def team(request):
    territories = Territory.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            "cities",
            queryset=City.objects.filter(is_active=True),
            to_attr="active_cities",
        ),
        Prefetch(
            "employees",
            queryset=public_employees(),
            to_attr="public_employees",
        ),
    )

    context = {
        "territories": territories,
        "employees": public_employees().prefetch_related(
            Prefetch(
                "territories",
                queryset=Territory.objects.filter(is_active=True),
                to_attr="active_territories",
            )
        ),
    }
    return render(request, "team/team.html", context)
