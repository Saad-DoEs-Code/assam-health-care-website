# Assam Healthcare website — developer handoff

Django 6.1 · Python 3.12 · SQLite · server-rendered templates with vanilla JavaScript.

## Run locally (Windows / PowerShell)

```powershell
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # once, for /admin/
python manage.py runserver
```

Without environment variables the site runs in development mode (`DEBUG=True`,
development secret key, console email). Visit http://127.0.0.1:8000/.

To try changes against a copy of the database without touching the real one:

```powershell
Copy-Item db.sqlite3 $env:TEMP\qa.sqlite3
$env:DJANGO_DB_PATH = "$env:TEMP\qa.sqlite3"
python manage.py runserver
```

## Checks and tests

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Tests live in each app's `tests.py`; shared test-data helpers are in
`apps/core/testing.py`.

## Site structure

| URL | View | Notes |
| --- | --- | --- |
| `/` | `apps.home.views.home` | Partners, categories, featured products, territories from the database |
| `/about/` | `apps.content.views.about` | Uses CMS page with slug `about` when published, otherwise built-in text |
| `/products/` | `apps.catalog.views.product_list` | `?q=`, `?category=`, `?company=`, `?page=` |
| `/products/<slug>/` | `apps.catalog.views.product_detail` | Public documents only |
| `/partners/` | `apps.companies.views.partner_list` | Official partners = `is_official_partner` |
| `/team/` | `apps.team.views.team` | Only `is_active` **and** `display_on_website` employees |
| `/careers/`, `/careers/<slug>/` | `apps.careers.views` | Published jobs whose deadline has not passed |
| `/contact/` | `apps.content.views.contact` | |
| `/inquiry/` | `apps.inquiries.views.create_inquiry` | Multi-product quotation form; `?product=<id>` preselects |
| `/pages/<slug>/` | `apps.content.views.page_detail` | Other published CMS pages |
| `/sitemap.xml`, `/robots.txt` | | Public, active content only |

"Public" products are defined once in `ProductQuerySet.public()`
(`apps/catalog/models.py`): product, category and company must all be active.

### Quotation form

* Items are a Django formset (`apps/inquiries/forms.py`), validated on the
  server against the public catalogue. One `Inquiry` and its `InquiryItem`s
  are saved in a single transaction.
* `static/js/inquiry_form.js` adds category filter, search, Add/Remove and
  duplicate warnings. Without JavaScript, three plain product rows are shown.
* The same product may appear more than once only with different variants.
* Limits: 50 products per request, quantity 1–1,000,000, notes 300 characters.
* Spam protection: hidden honeypot field; duplicate-submission token in the session.
* The whole public catalogue is sent to the page as JSON. That is fine for
  hundreds of products; if the catalogue grows to thousands, replace it with a
  small search endpoint.

## Content managed in Django Admin

Companies (partner flag, logo), categories, products (variants, images with a
single primary image, documents with "public" flag), territories, cities,
employees (display flag), inquiries with their items, jobs and applications,
CMS pages, and Site Settings (one record: name, tagline, phone, email,
WhatsApp, address, logo, favicon). Email and WhatsApp appear on the site only
when filled in.

## Production configuration

Settings are read from environment variables (see `.env.example`). Required:

| Variable | Purpose |
| --- | --- |
| `DJANGO_DEBUG` | Must be `False` |
| `DJANGO_SECRET_KEY` | Long random value; startup fails without it when DEBUG is False |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated domain names |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://` origins, comma-separated |

Optional: `DJANGO_DB_PATH`, `DJANGO_STATIC_ROOT`, `DJANGO_MEDIA_ROOT`,
`DJANGO_BEHIND_PROXY` (set when a proxy terminates TLS),
`DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SECURE_COOKIES`,
`DJANGO_SECURE_HSTS_SECONDS` (raise once HTTPS is confirmed working),
`DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`, `DJANGO_LOG_LEVEL`, and the
`DJANGO_EMAIL_*` variables.

Generate a secret key:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### Deployment steps

```powershell
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

Then serve the project with a production WSGI server (for example gunicorn on
Linux or waitress on Windows — neither is installed yet) behind a web server
that:

* serves `STATIC_ROOT` at `/static/`;
* serves `MEDIA_ROOT` at `/media/` **except** `/media/careers/` (CVs) and, ideally,
  `/media/catalog/products/documents/` files that are not public. Django only
  serves media itself when `DEBUG=True`.

`runserver` is a development server and must not be used in production.

`check --deploy` will still warn about `SECURE_HSTS_INCLUDE_SUBDOMAINS` and
`SECURE_HSTS_PRELOAD`; enable these only once the domain and all subdomains
are confirmed to be HTTPS-only.

## Known limitations

* No email notification for new inquiries or job applications; staff check
  Django Admin. (Email delivery is not configured.)
* Private product documents and CVs are hidden from pages, but anyone with the
  exact file URL can download them while `/media/` is served publicly. See the
  web-server note above.
* No rate limiting beyond the honeypot and duplicate-submission token.
* Categories have no image field (it was removed in migration `catalog.0006`).
* The inquiry form requires a city from the active city list.
