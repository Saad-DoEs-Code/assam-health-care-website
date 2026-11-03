# 🚀 Assam Healthcare — Website Launch Plan (Hostinger + Google Workspace)

> 💡 **How to use this page:** work through the phases **in order** — later phases depend on earlier ones. Tick each box when done and fill in the *Owner* / *Date* columns. **Never** write passwords, keys or App Passwords on this page; keep them in the password manager (Phase 0).

## 📌 Decisions already made

| Item | Decision | Notes |
| --- | --- | --- |
| Domain | **assamhealthcare.pk** — bought at Hostinger | USD 111.98 for 2 years · renewal due ≈ **November 2028** |
| Main website address | **https://assamhealthcare.pk** | `www.assamhealthcare.pk` redirects to it |
| Hosting | **Hostinger VPS** (KVM 1 is enough) | Hostinger's shared *Web/Cloud* plans **cannot run Django** — it needs a VPS |
| Server software | Ubuntu 24.04 · nginx · gunicorn · SQLite | Config files are in the project's `deploy/` folder |
| Email | **Google Workspace** (already owned) | Mailboxes like `info@assamhealthcare.pk`; the website also sends through it |

## 🗺️ Phase overview

| Phase | What it covers | Owner | Target date | Status |
| --- | --- | --- | --- | --- |
| 0 | Accounts & password manager | | | Not started |
| 1 | Business content & data | | | Not started |
| 2 | Domain (assamhealthcare.pk) | | | ✅ Bought |
| 3 | Google Workspace email on the new domain | | | Not started |
| 4 | Code repository (GitHub) | | | Not started |
| 5 | Buy & secure the Hostinger VPS | | | Not started |
| 6 | Deploy the website on the VPS | | | Not started |
| 7 | Point the domain & turn on HTTPS | | | Not started |
| 8 | Security hardening | | | Not started |
| 9 | Backups & monitoring | | | Not started |
| 10 | Google Search & Business Profile | | | Not started |
| 11 | Pre-launch testing | | | Not started |
| 12 | Launch day | | | Not started |
| 13 | First 30 days | | | Not started |
| 14 | Ongoing maintenance | | | Ongoing |

## 💰 Running costs (check current prices at checkout)

| Item | Cost | Renewal |
| --- | --- | --- |
| Domain assamhealthcare.pk | USD 111.98 / 2 years (paid) | Compare the renewal price before it auto-renews |
| Hostinger VPS KVM 1 | Hostinger advertises from about USD 6.49/month on a 24-month term (promotional; renews higher) | Check before renewal |
| Google Workspace | Existing subscription | — |
| SSL certificate | Free (Let's Encrypt, auto-renews) | Automatic |

---

## Phase 0 — Accounts & password manager

> 🎯 **Goal:** every login is owned by the company and stored safely.

- [ ] Decide who **owns** the website (content, replies to quotes) and who **maintains** it (server, updates, backups)
- [ ] Set up a **company password manager** (e.g. Bitwarden or 1Password) with a shared "Website" vault
- [ ] Turn on **2-step verification** for Hostinger, Google Workspace admin and GitHub

**Accounts register** (account names only — passwords stay in the password manager):

| Service | Login | Owner | 2-step on? |
| --- | --- | --- | --- |
| Hostinger (domain + VPS) | | | |
| Google Workspace admin | | | |
| GitHub | | | |
| VPS user `assam` (SSH key) | | | |
| Django admin (superuser) | | | |
| Google Search Console | | | |
| Google Business Profile | | | |

---

## Phase 1 — Business content & data

> 🎯 **Goal:** the site shows complete, accurate information. Do this in Django Admin (works on your computer now; the database is uploaded to the server in Phase 6).

**Company information**
- [ ] **Site Settings** — company name, tagline, phone, address; add **email** `info@assamhealthcare.pk` and the **WhatsApp** number
- [ ] Upload the **logo** and **favicon**
- [ ] Publish the **CEO / leadership message** (name, exact title, photo, message)
- [ ] Write 5–10 **help assistant answers** (Admin → Content → Assistant answers) for the questions customers ask most — delivery areas, how quotations work, payment/ordering process, office hours. No prices. Add the sales **WhatsApp number** in Site Settings so the assistant can offer WhatsApp

**Partners & catalogue**
- [ ] Add **Jassh Pharma** and tick *Official partner*
- [ ] Upload partner logos (Bain Medical, Marflow, Jassh Pharma)
- [ ] Add products with descriptions, sizes/variants and **real photos**
- [ ] Upload brochures/IFUs and tick *Is public* only for customer-facing documents
- [ ] ⚠️ Remove the private file **"Saad_Domicile.jpeg"** attached to *Dialyzer Brochure*
- [ ] Mark 3–6 products as **Featured**

**Sales coverage & protection**
- [ ] Add every **city** you serve (only *Multan* exists — other customers cannot submit the quote form)
- [ ] Add sales team members; tick *Display on website* only with their consent (phone/email become public)
- [ ] Add known competitors to the **Watchlist**; run **Re-run risk check** on existing inquiries
- [ ] Delete old test inquiries (e.g. "dagsj", "xxxxxxx")

**Legal & compliance**
- [ ] Publish a **Privacy Policy** as a CMS Page (slug `privacy-policy`)
- [ ] Confirm product listings and claims match your DRAP licences/registrations (ask your adviser)
- [ ] Confirm permission to show partner names/logos as official distribution partners

---

## Phase 2 — Domain ✅

- [x] Buy **assamhealthcare.pk** at Hostinger (2 years)
- [ ] Hostinger hPanel → **Domains → assamhealthcare.pk**: confirm the registrant is the **company**, with the company email and phone
- [ ] Turn on **auto-renew** and any domain protection Hostinger offers
- [ ] Note the exact renewal date: ____________
- [ ] Keep the domain on **Hostinger's nameservers** (all DNS records in Phases 3 and 7 are added in hPanel → *DNS / Nameservers*)

---

## Phase 3 — Google Workspace email on assamhealthcare.pk

> 🎯 **Goal:** staff email `@assamhealthcare.pk` works and lands in inboxes, not spam.
> 📌 If your Google Workspace already uses a different domain, add this one in **Admin console → Account → Domains → Manage domains → Add a domain**: choose **"User alias domain"** (every user automatically gets *name@assamhealthcare.pk*) or **"Secondary domain"** (separate users). You can switch the primary domain later if you want all mail on the new name.

**Verify the domain and route mail to Google** (records added in Hostinger hPanel → DNS)
- [ ] Add the **TXT verification record** Google shows, then click *Verify* in the Admin console
- [ ] Delete any existing **MX** records Hostinger created for its own email
- [ ] Add Google's **MX** record exactly as the Admin console shows (for new setups this is `smtp.google.com`, priority 1)
- [ ] Add **SPF** (TXT on `@`): `v=spf1 include:_spf.google.com ~all` — if a `v=spf1` record already exists, merge into one, never two
- [ ] Turn on **DKIM**: Admin console → *Apps → Google Workspace → Gmail → Authenticate email* → generate key → add the `google._domainkey` TXT record → *Start authentication*
- [ ] Add **DMARC** (TXT on `_dmarc`): `v=DMARC1; p=none; rua=mailto:it@assamhealthcare.pk` — after a month of clean reports change `p=none` to `p=quarantine`
- [ ] Send test emails to and from Gmail/Outlook; check they arrive and are not marked spam

**Mailboxes**
- [ ] Create or alias: `info@`, `sales@`, `careers@`, `it@` (receives website error reports) and **`website@`** (used by the website to send)
- [ ] Put `info@assamhealthcare.pk` in **Site Settings → Email**

**Let the website send email through Google**
- [ ] Turn on **2-Step Verification** for `website@assamhealthcare.pk`
- [ ] Create an **App Password** for it (Google Account → Security → App passwords) and store it in the password manager. If App Passwords are unavailable, the Workspace admin may need to allow them, or use Google's *SMTP relay* service instead
- [ ] These values go into the server environment file in Phase 6 (`DJANGO_EMAIL_*`, `DJANGO_ADMINS`)
- [ ] 📌 Google limits sending per mailbox per day — fine for error reports and quote alerts; a future **newsletter** should use a dedicated service (e.g. Brevo, Amazon SES)

---

## Phase 4 — Code repository (GitHub)

- [ ] Create a **private** GitHub repository under a company-owned account
- [ ] Push the code from your computer:
  ```bash
  git remote add origin https://github.com/<company-account>/<repo-name>.git
  git push -u origin main
  ```
- [ ] Confirm `db.sqlite3`, `media/` and `node_modules/` are **not** in the repository (excluded by `.gitignore`)
- [ ] For the server to download a private repo: GitHub → repo → *Settings → Deploy keys* → add the VPS's public key (read-only) — done in Phase 6

---

## Phase 5 — Buy & secure the Hostinger VPS

> 🎯 **Goal:** a clean Ubuntu server that only you can log into.

**Buy**
- [ ] Hostinger → **VPS Hosting → KVM 1** (1 vCPU, 4 GB RAM, 50 GB NVMe is plenty)
- [ ] Operating system: **Ubuntu 24.04** — the plain OS, **not** a control-panel or app template (it ships Python 3.12, which Django 6.1 needs)
- [ ] Data centre: the location **closest to Pakistan** Hostinger offers
- [ ] Add your **SSH public key** during setup (or set a strong root password temporarily)
- [ ] Note the server's **IPv4 address**: ____________

**First login and basic security** (from your computer: `ssh root@<server-ip>`)
- [ ] Update the system and create the app user:
  ```bash
  apt update && apt upgrade -y
  adduser assam
  usermod -aG sudo assam
  mkdir -p /home/assam/.ssh && cp ~/.ssh/authorized_keys /home/assam/.ssh/
  chown -R assam:assam /home/assam/.ssh
  ```
- [ ] Install the server software and firewall:
  ```bash
  apt install -y python3-venv python3-pip git nginx certbot python3-certbot-nginx unattended-upgrades
  ufw allow OpenSSH
  ufw allow 'Nginx Full'
  ufw enable
  dpkg-reconfigure -plow unattended-upgrades   # choose "Yes" for automatic security updates
  ```
- [ ] Open a **new** terminal and check `ssh assam@<server-ip>` works **before** the next step
- [ ] Disable root and password logins: in `/etc/ssh/sshd_config` set `PermitRootLogin no` and `PasswordAuthentication no`, then `sudo systemctl restart ssh`

---

## Phase 6 — Deploy the website on the VPS

> 🎯 **Goal:** the site runs on the server with gunicorn behind nginx. Run these as **`assam`** (`ssh assam@<server-ip>`).

**Code, packages, data**
- [ ] Create a deploy key and add it to GitHub (Phase 4), then clone:
  ```bash
  ssh-keygen -t ed25519 -C "assam-vps"    # press Enter for defaults
  cat ~/.ssh/id_ed25519.pub                # paste into GitHub → Deploy keys
  git clone git@github.com:<company-account>/<repo-name>.git ~/assam_healthcare
  python3 -m venv ~/venv
  ~/venv/bin/pip install -r ~/assam_healthcare/requirements.txt
  ```
- [ ] From **your computer** (in the project folder), upload the database and uploaded files:
  ```bash
  scp db.sqlite3 assam@<server-ip>:~/assam_healthcare/
  scp -r media assam@<server-ip>:~/assam_healthcare/
  ```

**Production settings**
- [ ] Generate a secret key and save it in the password manager:
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(50))"
  ```
- [ ] Choose a private admin address (e.g. `manage-k7p2x`) and save it in the password manager — it goes in `DJANGO_ADMIN_URL`; the admin is then at `https://assamhealthcare.pk/manage-k7p2x/`
- [ ] Create the environment file from the template and fill it in (secret key, admin address, Google App Password):
  ```bash
  sudo cp ~/assam_healthcare/deploy/assam_healthcare.env.example /etc/assam_healthcare.env
  sudo nano /etc/assam_healthcare.env
  sudo chown root:assam /etc/assam_healthcare.env
  sudo chmod 640 /etc/assam_healthcare.env
  ```
- [ ] Prepare the database and static files:
  ```bash
  cd ~/assam_healthcare
  set -a; source /etc/assam_healthcare.env; set +a
  ~/venv/bin/python manage.py migrate
  ~/venv/bin/python manage.py collectstatic --noinput
  ~/venv/bin/python manage.py createsuperuser     # strong password → password manager
  ```

**Start the services**
- [ ] Let nginx read static/media files and start the app:
  ```bash
  sudo usermod -aG assam www-data
  sudo cp ~/assam_healthcare/deploy/gunicorn.service /etc/systemd/system/assam_healthcare.service
  sudo systemctl daemon-reload
  sudo systemctl enable --now assam_healthcare
  sudo cp ~/assam_healthcare/deploy/nginx.conf /etc/nginx/sites-available/assam_healthcare
  sudo ln -s /etc/nginx/sites-available/assam_healthcare /etc/nginx/sites-enabled/
  sudo rm -f /etc/nginx/sites-enabled/default
  sudo nginx -t && sudo systemctl restart nginx
  ```
- [ ] Allow the update script to restart the site without a password:
  ```bash
  echo "assam ALL=NOPASSWD: /usr/bin/systemctl restart assam_healthcare" | sudo tee /etc/sudoers.d/assam_healthcare
  ```
- [ ] Check the app is running: `sudo systemctl status assam_healthcare` (logs: `sudo journalctl -u assam_healthcare -f`)

> ⚠️ **CVs are private:** nginx never serves `/media/careers/`. The CV link in admin will not open on the live site; download CVs with `scp` or ask the developer for a staff-only download page.
> ⚠️ **Private product documents** in `media/catalog/products/documents/` can be opened by anyone with the exact link — upload only public documents until a protected download page exists.

**Every future update** (after pushing new code to GitHub):
- [ ] `bash ~/assam_healthcare/deploy/update.sh` — backs up, pulls, installs, migrates, collects static files, runs the deploy check and restarts

---

## Phase 7 — Point the domain & turn on HTTPS

> 🎯 **Goal:** https://assamhealthcare.pk opens the site with a padlock.

- [ ] Hostinger hPanel → **Domains → assamhealthcare.pk → DNS**: delete Hostinger's default "parking" **A** / **CNAME** records for `@` and `www`
- [ ] Add **A** record `@` → `<server-ip>` and **A** record `www` → `<server-ip>` (TTL 3600 or default)
- [ ] Wait until both names resolve to the server (`nslookup assamhealthcare.pk` — can take from minutes to a few hours for `.pk`)
- [ ] Get the free certificate (also sets up auto-renewal and the HTTP → HTTPS redirect):
  ```bash
  sudo certbot --nginx -d assamhealthcare.pk -d www.assamhealthcare.pk --redirect
  sudo certbot renew --dry-run
  ```
- [ ] Test that `http://assamhealthcare.pk`, `http://www.…` and `https://www.…` all end at **https://assamhealthcare.pk**

---

## Phase 8 — Security hardening

- [ ] `~/venv/bin/python manage.py check --deploy` (with the env file loaded) shows only the HSTS warning
- [ ] After a week of working HTTPS: set `DJANGO_SECURE_HSTS_SECONDS=31536000` in `/etc/assam_healthcare.env`, then `sudo systemctl restart assam_healthcare`
- [ ] Visit a missing page — the friendly 404 must appear, never a technical error page
- [ ] Give each staff member their **own** admin login with only the permissions they need; no shared accounts
- [ ] Confirm root SSH login and password login are disabled (Phase 5)
- [ ] Confirm automatic security updates are on (`unattended-upgrades`)
- [ ] Optional: `sudo apt install fail2ban` to block repeated SSH login attempts
- [ ] Check the brute-force protection: 10 wrong admin passwords in a row should show **"Sign-in is paused"** for 15 minutes
- [ ] Check the response headers at https://securityheaders.com — expect a grade of A (Content-Security-Policy, Permissions-Policy, X-Frame-Options and, once enabled, HSTS)

---

## Phase 9 — Backups & monitoring

> 🎯 **Goal:** you can recover from mistakes and hear about outages first.

- [ ] Schedule the daily backup (database + uploads, keeps 14 days) — as `assam`, run `crontab -e` and add:
  ```
  30 2 * * * bash /home/assam/assam_healthcare/deploy/backup.sh >> /home/assam/backups/backup.log 2>&1
  15 3 * * * cd /home/assam/assam_healthcare && set -a && . /etc/assam_healthcare.env && /home/assam/venv/bin/python manage.py clearsessions
  ```
  The second line deletes expired visitor sessions every night, so form submissions from bots cannot slowly fill up the database
- [ ] Run it once by hand: `bash ~/assam_healthcare/deploy/backup.sh` and check `~/backups/`
- [ ] **Weekly:** copy backups **off the server** to company storage (from your computer):
  ```bash
  scp -r assam@<server-ip>:~/backups ./assam-backups
  ```
- [ ] Also enable **Hostinger VPS snapshots/backups** in hPanel if your plan includes them
- [ ] **Test a restore** once on a computer (open the backup database locally)
- [ ] Set up free **uptime monitoring** (e.g. UptimeRobot) for https://assamhealthcare.pk → alerts to `it@`
- [ ] Error reports arrive by email at `it@assamhealthcare.pk` (from `DJANGO_ADMINS`); server logs: `sudo journalctl -u assam_healthcare` and `/var/log/nginx/assam_healthcare.error.log`

---

## Phase 10 — Google Search & Business Profile

**Google Search Console**
- [ ] Add a **Domain property** for `assamhealthcare.pk`, verify with the TXT record in Hostinger DNS
- [ ] Submit the sitemap: `https://assamhealthcare.pk/sitemap.xml`
- [ ] Check `https://assamhealthcare.pk/robots.txt` opens
- [ ] After a week, review *Pages* for errors

**Google Business Profile** (use the company Google Workspace account)
- [ ] Create/claim **Assam Healthcare (Pvt.) Ltd.** — Street #3, Al-Raheem Colony, Nishter Road, Multan · 0300-9631291
- [ ] Category close to *Medical supply store* / *Medical equipment supplier*; add website https://assamhealthcare.pk, hours, logo, office photos
- [ ] Complete Google's verification (video, phone or postcard — Google chooses)
- [ ] Ask satisfied customers for genuine reviews (never buy or write reviews)

**Other presence**
- [ ] Bing Webmaster Tools (import from Search Console)
- [ ] LinkedIn company page and Facebook page with the website link
- [ ] WhatsApp Business profile on the sales number with the website link
- [ ] Add the website and `@assamhealthcare.pk` emails to letterheads, quotations, signatures and visiting cards

---

## Phase 11 — Pre-launch testing (on https://assamhealthcare.pk)

- [ ] Every page opens: Home, About, Products, Partners, Sales Team, Careers, Contact
- [ ] Search, category filter, pagination work; product **Request a Quote** preselects the product
- [ ] Submit a quote with several products/sizes → reference number shown → visible in Admin with a risk level
- [ ] Marking that inquiry **Quoted** without verification is refused; verifying with a note allows it
- [ ] Check on a real **phone**: menu, quote form, images, no sideways scrolling
- [ ] `https://assamhealthcare.pk/does-not-exist` shows the friendly 404
- [ ] Trigger a test error email: `~/venv/bin/python manage.py sendtestemail --admins` (env file loaded) → arrives at `it@`
- [ ] Delete test inquiries afterwards

---

## Phase 12 — Launch day

- [ ] Run a backup **before** announcing
- [ ] Announce to customers (WhatsApp, email) with the link
- [ ] Update Google Business Profile, LinkedIn, Facebook
- [ ] Brief the sales team: where quotes appear, the verification rule, marking competitors

---

## Phase 13 — First 30 days

- [ ] Check Admin → Inquiries **every working day**
- [ ] Review risk flags weekly; add confirmed competitors to the Watchlist
- [ ] Review Search Console and uptime alerts
- [ ] Collect feedback from 3–5 customers
- [ ] Choose next features: **email alerts for new quotes**, **newsletter / product updates**, inquiry notes & CSV export, automatic assignment to territory reps, protected CV/document downloads

---

## Phase 14 — Ongoing maintenance

**Weekly** — copy backups off the server · review inquiries and the watchlist
**Monthly** — update products/photos/team · check uptime and error emails · Search Console · `sudo apt update && sudo apt upgrade`
**Quarterly** — Django/Pillow/gunicorn security updates (developer updates `requirements.txt`, runs tests, then `deploy/update.sh`) · test a restore · review admin users
**Yearly** — check Hostinger VPS and domain renewals (domain due ≈ Nov 2028) · review the Privacy Policy and partner/regulatory claims

---

> 📚 **Technical references in the project:** `DEPLOYMENT.md` (settings), `deploy/` (server config, update and backup scripts), `deploy/assam_healthcare.env.example` (all production settings), `FRONTEND.md` (styling and images).
