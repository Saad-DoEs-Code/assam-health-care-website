# Assam Healthcare website

Website of **Assam Healthcare (Pvt.) Ltd.**, Multan — distributor of medical
consumables, surgical disposables, medical devices and dialysis products.
*Quality. Trust. Service.*

Visitors browse the product catalogue and send one quotation request for many
products; staff manage products, requests, vacancies and site content in the
Django admin. Prices are never shown online.

**Stack:** Django 6.1 · Python 3.12 · SQLite · server-rendered templates ·
Tailwind CSS (pre-built) · vanilla JavaScript.

## Quick start

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_staff_roles
python manage.py createsuperuser
python manage.py runserver
```

Run the tests with `python manage.py test`.

## Documentation

| File | Contents |
|---|---|
| [DEPLOYMENT.md](DEPLOYMENT.md) | Settings, production setup on the Hostinger VPS, protections, known limitations |
| [FRONTEND.md](FRONTEND.md) | Tailwind CSS build, fonts and design tokens |
| [LAUNCH_CHECKLIST.md](LAUNCH_CHECKLIST.md) | Step-by-step launch plan (domain, email, server, SEO) |
| [deploy/](deploy/) | Server configuration, update and backup scripts |

## Main features

- Product catalogue with categories, partners, search and variants
- Multi-product quotation requests with competitor screening and a
  verification step before prices are shared
- Careers page with CV upload; sales team and coverage pages
- "Need help?" assistant with product search and admin-managed answers
- Rate limits, Content-Security-Policy and hardened nginx configuration

Developed by [saad.does.code@gmail.com](mailto:saad.does.code@gmail.com).
