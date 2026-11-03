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

Styling uses Tailwind CSS. The compiled `static/css/site.css` is committed; to
change styles, install Node.js and see [FRONTEND.md](FRONTEND.md)
(`npm install`, then `npm run build:css` or `npm run watch:css`).

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

### Quotation screening (competitor protection)

Every quotation request is checked automatically (`apps/inquiries/screening.py`)
and given a **risk level** with reasons, shown in Django Admin → Inquiries:

* **High:** matches the **Watchlist** (phone, email, email domain, organisation
  name or keyword), or uses the phone/email of an inquiry already marked as a
  competitor.
* **Points** (2+ = medium, 4+ = high): distributor / trader (2), same phone or
  email used before under a different name or organisation (2), broad request —
  10+ products or 4+ categories (2), 3+ requests from one contact in 30 days
  (1), free email address (1).
* **Returning customers** (an earlier inquiry from the same phone/email was
  converted) are marked and kept low risk unless on the watchlist.

Staff workflow: verify the requester (call back, letterhead), tick **Is
verified** and add a note — an inquiry cannot be marked *Quoted* or *Converted*
until verified. The action **Mark as suspected competitor** closes the inquiry
and adds its phone, WhatsApp, email and organisation to the watchlist. **Re-run
risk check** re-screens selected inquiries (e.g. older ones, or after editing
the watchlist). Requesters always see the same confirmation page.

## Content managed in Django Admin

Companies (partner flag, logo), categories, products (variants, images with a
single primary image, documents with "public" flag), territories, cities,
employees (display flag), inquiries with their items, jobs and applications,
CMS pages, a leadership (CEO) message — shown on the homepage and About
page only while published — and Site Settings (one record: name, tagline, phone, email,
WhatsApp, address, logo, favicon). Email and WhatsApp appear on the site only
when filled in.

## Production configuration

Settings are read from environment variables. For the Hostinger VPS, all of
them are in `deploy/assam_healthcare.env.example` (installed as
`/etc/assam_healthcare.env`). Required:

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
`DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`, `DJANGO_LOG_LEVEL`, the
`DJANGO_EMAIL_*` variables, `DJANGO_ADMINS` (comma-separated addresses that
receive error reports), `DJANGO_ADMIN_URL` (admin address, default `admin/`;
use a private word in production) and `DJANGO_CACHE_DIR` (shared file cache
for the rate limits; without it each gunicorn worker counts separately).

## Protection against abuse

* **Rate limits in Django** (`apps/core/ratelimit.py`), per IP address:
  10 quotation requests and 5 job applications an hour (further attempts get
  a polite "too many requests" message, status 429, and nothing is saved),
  and admin sign-in pauses for 15 minutes after 10 wrong passwords.
* **Rate limits in nginx** (`deploy/nginx.conf`): 10 page requests a second
  (burst 40) and 10 form submissions a minute per IP; requests for unknown
  host names, hidden files and `.php`-style scanner URLs never reach Django.
* **Content-Security-Policy** (`SECURE_CSP` in settings): only this site's own
  scripts run. Keep JavaScript in `static/js/` — inline `<script>` blocks are
  blocked by the browser.
* Uploaded media is served with a sandboxing CSP, so an uploaded HTML/SVG file
  cannot run scripts on the site.
* Phone numbers typed with Urdu/Arabic digits are converted to 0-9 before they
  are saved, so the competitor screening always matches them.

Generate a secret key:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### Hosting: Hostinger VPS

The live site runs on a **Hostinger VPS** (Ubuntu 24.04, Python 3.12) at
**https://assamhealthcare.pk**. Hostinger's shared Web/Cloud hosting cannot run
Django. Step-by-step instructions (server setup, DNS, HTTPS, Google Workspace
email, backups) are in [LAUNCH_CHECKLIST.md](LAUNCH_CHECKLIST.md).

| File in `deploy/` | Installed as | Purpose |
| --- | --- | --- |
| `assam_healthcare.env.example` | `/etc/assam_healthcare.env` (root:assam, 640) | Production settings and secrets |
| `gunicorn.service` | `/etc/systemd/system/assam_healthcare.service` | Runs Django with gunicorn on a Unix socket |
| `nginx.conf` | `/etc/nginx/sites-available/assam_healthcare` | HTTPS, `www` → bare-domain redirect, static/media files, blocks `/media/careers/` |
| `update.sh` | run as `assam` | Backup → `git pull` → install → migrate → collectstatic → `check --deploy` → restart |
| `backup.sh` | daily cron as `assam` | Consistent SQLite copy + `media/` archive in `~/backups`, kept 14 days |

Deploy an update after pushing to GitHub:

```bash
bash ~/assam_healthcare/deploy/update.sh
```

The compiled CSS is committed, so Node.js is not needed on the server.
`runserver` is a development server and must never be used in production.

`check --deploy` warns about HSTS until `DJANGO_SECURE_HSTS_SECONDS` is set
(do this after HTTPS has worked for about a week). Enable
`SECURE_HSTS_INCLUDE_SUBDOMAINS` only if every subdomain uses HTTPS.

## Known limitations

* No email notification for new inquiries or job applications yet; staff check
  Django Admin. Email delivery (Google Workspace SMTP) is used for error reports.
* nginx never serves CVs (`/media/careers/`), so the CV link in admin does not
  open on the live site until a staff-only download view is added.
* Private product documents are hidden from pages, but anyone with the exact
  file URL can open them; upload only public documents for now.
* Rate limits are per IP address. Visitors sharing one mobile-network address
  share the limits, which are set high enough for normal use.
* Categories have no image field (it was removed in migration `catalog.0006`).
* The inquiry form requires a city from the active city list.
