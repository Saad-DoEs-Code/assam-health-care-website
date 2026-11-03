"""
Screening of quotation requests.

Every new inquiry gets a risk level (low / medium / high) and a list of
human-readable reasons, shown to staff in the admin. The aim is to help the
sales team spot requests from competitors fishing for prices; the check
never blocks a submission and the requester is never told the result.

Strong signals (a watchlist match, or a contact previously marked as a
competitor) always mean high risk. Other signals add points.
"""

import re
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from apps.content.context_processors import phone_to_international

# Common free email providers. A free address is only a weak signal: many
# genuine hospital buyers in Pakistan use them.
FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "yahoo.co.uk",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "msn.com",
    "icloud.com",
    "aol.com",
    "proton.me",
    "protonmail.com",
    "yandex.com",
    "mail.com",
}

BROAD_REQUEST_ITEMS = 10
BROAD_REQUEST_CATEGORIES = 4
FREQUENCY_WINDOW_DAYS = 30
FREQUENCY_LIMIT = 3  # requests from one contact within the window, including this one

POINTS_DISTRIBUTOR = 2
POINTS_IDENTITY_MISMATCH = 2
POINTS_BROAD_REQUEST = 2
POINTS_FREQUENT = 1
POINTS_FREE_EMAIL = 1

HIGH_RISK_POINTS = 4
MEDIUM_RISK_POINTS = 2


def normalize_phone(phone):
    """Digits in +92 format, or "" when there are no digits."""
    return phone_to_international(phone or "")


def normalize_text(value):
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def email_domain(email):
    email = (email or "").strip().lower()
    return email.rsplit("@", 1)[1] if "@" in email else ""


def normalize_identifier(kind, value):
    """Normalised form of a watchlist value, used for matching."""
    from apps.inquiries.models import WatchlistEntry

    if kind == WatchlistEntry.KIND_PHONE:
        return normalize_phone(value) or normalize_text(value)
    if kind == WatchlistEntry.KIND_EMAIL_DOMAIN:
        return normalize_text(value).lstrip("@")
    return normalize_text(value)


def _watchlist_reasons(inquiry):
    from apps.inquiries.models import WatchlistEntry

    entries = WatchlistEntry.objects.filter(is_active=True)
    phones = {normalize_phone(inquiry.phone), normalize_phone(inquiry.whatsapp)} - {""}
    email = normalize_text(inquiry.email)
    domain = email_domain(inquiry.email)
    organization = normalize_text(inquiry.organization)
    free_text = " ".join(
        normalize_text(value)
        for value in (inquiry.name, inquiry.organization, inquiry.designation, inquiry.message)
    )

    reasons = []
    for entry in entries:
        value = entry.normalized_value
        if not value:
            continue
        matched = (
            (entry.kind == WatchlistEntry.KIND_PHONE and value in phones)
            or (entry.kind == WatchlistEntry.KIND_EMAIL and email and value == email)
            or (entry.kind == WatchlistEntry.KIND_EMAIL_DOMAIN and domain and value == domain)
            or (entry.kind == WatchlistEntry.KIND_ORGANIZATION and organization and value in organization)
            or (entry.kind == WatchlistEntry.KIND_KEYWORD and value in free_text)
        )
        if matched:
            detail = f" — {entry.reason}" if entry.reason else ""
            reasons.append(f"Watchlist match: {entry.get_kind_display().lower()} “{entry.value}”{detail}")
    return reasons


def _earlier_inquiries(inquiry):
    """Other inquiries from the same phone, WhatsApp number or email."""
    from apps.inquiries.models import Inquiry

    phones = {normalize_phone(inquiry.phone), normalize_phone(inquiry.whatsapp)} - {""}
    condition = Q()
    if phones:
        condition |= Q(phone_normalized__in=phones)
    if inquiry.email:
        condition |= Q(email__iexact=inquiry.email.strip())
    if not condition:
        return Inquiry.objects.none()
    return Inquiry.objects.filter(condition).exclude(pk=inquiry.pk)


def assess_inquiry(inquiry):
    """
    Work out the risk level for a saved inquiry.

    Returns (risk_level, reasons, is_returning_customer).
    """
    from apps.inquiries.models import Inquiry

    reasons = []
    strong = False
    points = 0

    watchlist_reasons = _watchlist_reasons(inquiry)
    if watchlist_reasons:
        strong = True
        reasons += watchlist_reasons

    earlier = list(_earlier_inquiries(inquiry))

    if any(previous.is_suspected_competitor for previous in earlier):
        strong = True
        reasons.append("Same phone or email as an inquiry marked as a competitor")

    converted = [previous for previous in earlier if previous.status == "converted"]
    is_returning = bool(converted)
    if is_returning:
        reasons.append(f"Returning customer (inquiry #{converted[0].pk} was converted)")

    name = normalize_text(inquiry.name)
    organization = normalize_text(inquiry.organization)
    mismatched = [
        previous
        for previous in earlier
        if normalize_text(previous.name) != name
        or (
            organization
            and normalize_text(previous.organization)
            and normalize_text(previous.organization) != organization
        )
    ]
    if mismatched:
        points += POINTS_IDENTITY_MISMATCH
        reasons.append(
            "Phone or email used before under a different name or organisation "
            f"(inquiry #{mismatched[0].pk})"
        )

    window_start = timezone.now() - timedelta(days=FREQUENCY_WINDOW_DAYS)
    recent = [previous for previous in earlier if previous.created_at >= window_start]
    if len(recent) + 1 >= FREQUENCY_LIMIT:
        points += POINTS_FREQUENT
        reasons.append(
            f"{len(recent) + 1} requests from this contact in the last "
            f"{FREQUENCY_WINDOW_DAYS} days"
        )

    if inquiry.organization_type == "distributor":
        points += POINTS_DISTRIBUTOR
        reasons.append("Organisation type is distributor / trader")

    items = list(inquiry.items.select_related("product"))
    category_count = len({item.product.category_id for item in items})
    if len(items) >= BROAD_REQUEST_ITEMS or category_count >= BROAD_REQUEST_CATEGORIES:
        points += POINTS_BROAD_REQUEST
        reasons.append(
            f"Broad request: {len(items)} products across {category_count} categories"
        )

    if email_domain(inquiry.email) in FREE_EMAIL_DOMAINS and not is_returning:
        points += POINTS_FREE_EMAIL
        reasons.append("Free email address (common for genuine buyers too)")

    if strong:
        level = Inquiry.RISK_HIGH
    elif is_returning:
        level = Inquiry.RISK_LOW
    elif points >= HIGH_RISK_POINTS:
        level = Inquiry.RISK_HIGH
    elif points >= MEDIUM_RISK_POINTS:
        level = Inquiry.RISK_MEDIUM
    else:
        level = Inquiry.RISK_LOW

    return level, reasons, is_returning


def screen_inquiry(inquiry):
    """Assess an inquiry and save the result on it."""
    level, reasons, is_returning = assess_inquiry(inquiry)
    inquiry.risk_level = level
    inquiry.risk_reasons = "\n".join(reasons)
    inquiry.is_returning_customer = is_returning
    inquiry.save(update_fields=["risk_level", "risk_reasons", "is_returning_customer", "updated_at"])
    return inquiry


def mark_as_competitor(inquiry, user=None):
    """
    Close an inquiry as a suspected competitor and add its phone numbers,
    email and organisation to the watchlist so later attempts are flagged.

    Returns the number of new watchlist entries.
    """
    from apps.inquiries.models import WatchlistEntry

    reason = f"Marked as competitor from inquiry #{inquiry.pk}"
    candidates = [
        (WatchlistEntry.KIND_PHONE, inquiry.phone),
        (WatchlistEntry.KIND_PHONE, inquiry.whatsapp),
        (WatchlistEntry.KIND_EMAIL, inquiry.email),
        (WatchlistEntry.KIND_ORGANIZATION, inquiry.organization),
    ]

    created = 0
    for kind, value in candidates:
        if not (value or "").strip():
            continue
        normalized = normalize_identifier(kind, value)
        if WatchlistEntry.objects.filter(kind=kind, normalized_value=normalized).exists():
            continue
        WatchlistEntry.objects.create(
            kind=kind,
            value=value.strip(),
            reason=reason,
            source_inquiry=inquiry,
            created_by=user,
        )
        created += 1

    inquiry.is_suspected_competitor = True
    inquiry.status = "closed"
    inquiry.save(update_fields=["is_suspected_competitor", "status", "updated_at"])
    screen_inquiry(inquiry)
    return created
