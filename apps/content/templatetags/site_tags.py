from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from django import template
from django.conf import settings
from django.db import DatabaseError
from django.templatetags.static import static

from apps.content.context_processors import phone_to_international
from apps.content.models import AssistantAnswer

register = template.Library()

CATEGORY_ART_DIR = "images/categories"
DEFAULT_CATEGORY_ART = f"{CATEGORY_ART_DIR}/default.svg"
CATEGORY_PHOTO_DIR = "images/photos/categories"


@register.filter
def tel_href(phone):
    """Turn "0300-1234567" into "tel:+923001234567" for phone links."""
    number = phone_to_international(phone)
    return f"tel:{number}" if number else ""


@lru_cache(maxsize=1)
def _available_category_art():
    """Slugs that have an illustration in static/images/categories/."""
    art_dir = Path(settings.BASE_DIR) / "static" / CATEGORY_ART_DIR
    return {path.stem for path in art_dir.glob("*.svg")}


@register.simple_tag
def category_art(category):
    """
    URL of the illustration for a category.

    Uses static/images/categories/<slug>.svg, then the parent category's
    artwork, then default.svg — so a new category added in the admin never
    points at a missing file.
    """
    available = _available_category_art()
    for candidate in (category, getattr(category, "parent", None)):
        if candidate is not None and candidate.slug in available:
            return static(f"{CATEGORY_ART_DIR}/{candidate.slug}.svg")
    return static(DEFAULT_CATEGORY_ART)


@lru_cache(maxsize=1)
def _available_category_photos():
    """Slugs that have a photo in static/images/photos/categories/."""
    photo_dir = Path(settings.BASE_DIR) / "static" / CATEGORY_PHOTO_DIR
    return {
        path.stem
        for path in photo_dir.glob("*.webp")
        if not path.stem.endswith("-480")
    }


@register.simple_tag
def category_photo(category):
    """
    Photo URLs for a category, or None when it has no photo.

    Returns {"src": 800px version, "src_small": 480px version}. Looks for the
    category's own slug, then its parent's. Templates fall back to the SVG
    illustration ({% category_art %}) when this returns None.
    """
    available = _available_category_photos()
    for candidate in (category, getattr(category, "parent", None)):
        if candidate is not None and candidate.slug in available:
            base = f"{CATEGORY_PHOTO_DIR}/{candidate.slug}"
            return {
                "src": static(f"{base}.webp"),
                "src_small": static(f"{base}-480.webp"),
            }
    return None


ASSISTANT_WHATSAPP_GREETING = (
    "Hello Assam Healthcare, I have a question about your products."
)


@register.inclusion_tag("partials/assistant.html", takes_context=True)
def help_assistant(context):
    """The help assistant (chat button) with the published answers."""
    company_contact = context.get("company_contact", {})
    whatsapp_href = company_contact.get("whatsapp_href", "")
    try:
        answers = list(AssistantAnswer.objects.filter(is_published=True))
    except DatabaseError:
        answers = []
    return {
        "company_contact": company_contact,
        "answers": answers,
        "whatsapp_href": whatsapp_href,
        "whatsapp_greeting_href": (
            f"{whatsapp_href}?text={quote(ASSISTANT_WHATSAPP_GREETING)}"
            if whatsapp_href
            else ""
        ),
    }
