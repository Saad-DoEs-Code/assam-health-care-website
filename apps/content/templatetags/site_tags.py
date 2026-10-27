from functools import lru_cache
from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static

from apps.content.context_processors import phone_to_international

register = template.Library()

CATEGORY_ART_DIR = "images/categories"
DEFAULT_CATEGORY_ART = f"{CATEGORY_ART_DIR}/default.svg"


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
