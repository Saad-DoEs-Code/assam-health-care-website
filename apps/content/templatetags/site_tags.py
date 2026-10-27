from django import template

from apps.content.context_processors import phone_to_international

register = template.Library()


@register.filter
def tel_href(phone):
    """Turn "0300-1234567" into "tel:+923001234567" for phone links."""
    number = phone_to_international(phone)
    return f"tel:{number}" if number else ""
