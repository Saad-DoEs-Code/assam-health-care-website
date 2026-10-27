# Frontend guide

The website is styled with **Tailwind CSS v4.3.3**, compiled by the official
Tailwind CLI into one static file, `static/css/site.css`, which Django serves
like any other static file. There is no JavaScript framework or bundler.

## Requirements

* Node.js 20 or newer (tested with Node 22) and npm — only needed to rebuild CSS.
* Python/Django as described in `DEPLOYMENT.md`.

## Commands

```powershell
npm install          # once: installs Tailwind CLI and the font packages
npm run build        # copies fonts + writes minified static/css/site.css
npm run build:css    # CSS only
npm run watch:css    # rebuild automatically while editing templates
```

Run `npm run build:css` (or keep `watch:css` running) after changing classes in
templates, `static/js/*.js` or `frontend/tailwind.css`, then reload the page.
The compiled `static/css/site.css` is committed, so a server that only runs
Django does not need Node.js — but the file must be rebuilt and committed
whenever styling changes.

During development, `python manage.py runserver` and `npm run watch:css` can
run side by side in two terminals.

## Files

| Path | Purpose |
| --- | --- |
| `frontend/tailwind.css` | Tailwind entry point: design tokens (`@theme`), base styles, shared components (`.btn`, form controls, `.rich-text`) |
| `frontend/copy-fonts.mjs` | Copies the self-hosted fonts from `node_modules` into `static/fonts/` |
| `static/css/site.css` | **Generated** — do not edit by hand |
| `static/fonts/` | Manrope and Source Serif 4 (SIL Open Font License) |
| `static/images/categories/` | Category illustrations (see below) |
| `static/js/main.js` | Mobile navigation |
| `static/js/inquiry_form.js` | Quotation form product picker |
| `templates/partials/` | Shared pieces: navbar, footer, breadcrumbs, page header, section heading, form field, quotation call to action |
| `templates/catalog/partials/` | Product card and category card |

## Design tokens

Defined in `@theme` in `frontend/tailwind.css`. Tailwind's default colour
palette is switched off, so only these colours exist:

* `navy-50 … navy-950` — `navy-700` is the brand primary `#153e75`, `navy-800` the brand dark `#102f59`.
* `teal-50 … teal-800` — `teal-600` is the brand teal `#0f8b8d` (fills, icons);
  use `teal-700` for teal **text** and for buttons with white text (contrast).
* `ink` (body text), `muted` (secondary text), `line` / `line-strong` (borders),
  `canvas` / `mist` (pale surfaces), `danger-*`, `success-*` (validation only).
* Fonts: `font-sans` (Manrope) for interface text, `font-display` (Source Serif 4) for headings.
* `--radius-card`, `--shadow-card`, `--shadow-lift`, `--container-page` — used as
  `rounded-(--radius-card)`, `shadow-(--shadow-card)`, `max-w-(--container-page)`.

## Rules for class names

Tailwind only generates classes it can find as complete strings in
`templates/`, `static/js/` and `apps/`. Never build class names from pieces
(`"bg-" + colour`); write the full class in the template or JavaScript, as
`inquiry_form.js` does for its buttons.

## Category illustrations

`static/images/categories/<category-slug>.svg` is shown for the category with
that slug. The `{% category_art category %}` tag (in
`apps/content/templatetags/site_tags.py`) falls back to the parent category's
illustration and then to `default.svg`, so a category added in the admin never
shows a broken image.

To add artwork for a new category, create `<slug>.svg` in the same style:
`viewBox="0 0 200 160"`, the white backdrop circle and ground shadow, 3–4 px
navy (`#153e75`) strokes with round caps, teal (`#0f8b8d`) highlights, no
scripts, raster images or external references. Restart Django afterwards (the
list of available files is cached).

Current illustrations: dialysis, urology, interventional-cardiology,
anesthesia-respiratory-care, gastroenterology-hepatobiliary, neurosurgery,
interventional-radiology-biopsy, general-surgery, diagnostics-equipment,
hygiene-disinfection, and default.
