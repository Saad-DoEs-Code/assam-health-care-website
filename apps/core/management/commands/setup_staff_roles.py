"""
Create the staff roles (admin groups) and their permissions.

    python manage.py setup_staff_roles

Safe to run again after updates: each role's permissions are reset to the
list below, so change roles here rather than in the admin. Give a staff
member a role in Admin -> Users -> (user) -> Groups, and tick "Staff status".
Superusers are not affected.
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

VIEW = ("view",)
EDIT = ("view", "change")
FULL = ("view", "add", "change", "delete")

CATALOGUE_READ = {
    "catalog.category": VIEW,
    "catalog.product": VIEW,
    "catalog.productvariant": VIEW,
    "companies.company": VIEW,
    "team.territory": VIEW,
    "team.city": VIEW,
    "team.employee": VIEW,
}

ROLES = {
    # Answers quotation requests: can update status, verify and add notes,
    # but cannot delete requests or change the competitor watchlist.
    "Sales representative": {
        "inquiries.inquiry": EDIT,
        "inquiries.inquiryitem": VIEW,
        "inquiries.watchlistentry": VIEW,
        **CATALOGUE_READ,
    },
    # Everything a representative can do, plus deleting requests and
    # managing the competitor watchlist.
    "Sales manager": {
        "inquiries.inquiry": FULL,
        "inquiries.inquiryitem": FULL,
        "inquiries.watchlistentry": FULL,
        **CATALOGUE_READ,
    },
    # Keeps the public website up to date. No access to customer data.
    "Content editor": {
        "catalog.category": FULL,
        "catalog.product": FULL,
        "catalog.productvariant": FULL,
        "catalog.productimage": FULL,
        "catalog.productdocument": FULL,
        "companies.company": FULL,
        "content.page": FULL,
        "content.leadershipmessage": FULL,
        "content.assistantanswer": FULL,
        "content.sitesettings": EDIT,
        "team.territory": FULL,
        "team.city": FULL,
        "team.employee": FULL,
    },
    # Publishes vacancies and reviews applications. No sales data.
    "HR": {
        "careers.job": FULL,
        "careers.jobapplication": ("view", "delete"),
    },
}


def permissions_for(model_actions):
    permissions = []
    for model_label, actions in model_actions.items():
        app_label, model = model_label.split(".")
        for action in actions:
            permissions.append(
                Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=f"{action}_{model}",
                )
            )
    return permissions


class Command(BaseCommand):
    help = "Create or update the staff roles (admin groups) and their permissions."

    def handle(self, *args, **options):
        for name, model_actions in ROLES.items():
            group, created = Group.objects.get_or_create(name=name)
            permissions = permissions_for(model_actions)
            group.permissions.set(permissions)
            verb = "Created" if created else "Updated"
            self.stdout.write(f"{verb} role '{name}' ({len(permissions)} permissions)")
        self.stdout.write(self.style.SUCCESS("Staff roles are ready."))
