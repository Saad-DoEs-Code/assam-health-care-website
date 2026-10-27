import re

from django.db import DatabaseError

from .models import SiteSettings

# Confirmed company details, used whenever SiteSettings is missing or a field
# has been left blank. Email and WhatsApp have no default on purpose: they are
# only shown when entered in Site Settings.
DEFAULT_COMPANY_NAME = "Assam Healthcare (Pvt.) Ltd."
DEFAULT_TAGLINE = "Quality. Trust. Service."
DEFAULT_PHONE = "0300-9631291"
DEFAULT_ADDRESS = "Street #3, Al-Raheem Colony, Nishter Road, Multan, Pakistan."


def phone_to_international(phone):
    """
    Convert a Pakistani phone number to +92 format for tel: and WhatsApp links.

    "0300-9631291" and "+92 300 9631291" both become "+923009631291".
    Returns an empty string when the value contains no digits.
    """
    digits = re.sub(r"\D", "", phone or "")
    if not digits:
        return ""
    if digits.startswith("0092"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = "92" + digits[1:]
    return "+" + digits


def site_settings(request):
    """
    Expose site settings (logo, company name, contact info) to all templates.

    `company_contact` always has usable values, so templates do not need to
    repeat fallback text.
    """
    try:
        settings_obj = SiteSettings.objects.first()
    except DatabaseError:
        settings_obj = None

    phone = (settings_obj.phone if settings_obj else "") or DEFAULT_PHONE
    whatsapp = settings_obj.whatsapp if settings_obj else ""
    whatsapp_number = phone_to_international(whatsapp)

    company_contact = {
        "name": (settings_obj.company_name if settings_obj else "") or DEFAULT_COMPANY_NAME,
        "tagline": (settings_obj.tagline if settings_obj else "") or DEFAULT_TAGLINE,
        "phone": phone,
        "phone_href": "tel:" + phone_to_international(phone),
        "address": (settings_obj.address if settings_obj else "") or DEFAULT_ADDRESS,
        "email": settings_obj.email if settings_obj else "",
        "whatsapp": whatsapp,
        "whatsapp_href": (
            "https://wa.me/" + whatsapp_number.lstrip("+") if whatsapp_number else ""
        ),
    }

    return {
        "site_settings": settings_obj,
        "company_contact": company_contact,
        # First URL segment ("products", "careers", ...) for highlighting
        # the current section in the navigation.
        "nav_section": request.path.strip("/").split("/")[0],
    }
