# HR Recruitment System — Project Documentation

**Grain Marketing Board (GMB) HR Portal**  
A Flask-based recruitment and applicant tracking system for posting jobs, screening candidates, scheduling interviews, and managing external interview panels.

---

## Table of Contents

1. [Overview](#overview)
2. [Portals & User Roles](#portals--user-roles)
3. [Main Features](#main-features)
4. [Project Structure](#project-structure)
5. [Where to Put Pictures & Media](#where-to-put-pictures--media)
6. [Installation & Running](#installation--running)
7. [Configuration](#configuration)
8. [Default Logins](#default-logins)
9. [Typical Workflows](#typical-workflows)
10. [Data Storage](#data-storage)
11. [API & Key Routes](#api--key-routes)
12. [Branding & Colors](#branding--colors)
13. [Troubleshooting](#troubleshooting)

---

## Overview

This system helps HR teams manage the full hiring lifecycle:

| Stage | What the system does |
|-------|----------------------|
| **Post jobs** | HR creates job listings with title, description, department, and positions needed |
| **Apply** | Candidates browse open jobs and submit applications with CV and certificates |
| **Screen** | CVs are scored and ranked against job requirements |
| **Interview** | HR schedules interviews and sends email invitations |
| **Score** | HR staff and external interviewers evaluate candidates on criteria |
| **Select** | Best candidates are shortlisted and notified |

**Tech stack:** Python 3, Flask, Jinja2 templates, JSON file storage, optional PostgreSQL hooks, SMTP email, scikit-learn CV scoring.

---

## Portals & User Roles

### 1. Applicant Portal (Public)
- **URL:** `http://localhost:5000/` or `/portal`
- **Who:** Job seekers (no login required)
- **Pages:** Job listings, job detail, application form, success page

### 2. HR Portal (Staff)
- **URL:** `http://localhost:5000/login` → `/hr`
- **Roles:**
  - **HR Manager** (`hr`) — full access, user management, settings
  - **HR Staff** (`hr_staff`) — screening/scoring based on permissions
- **Sections:** Dashboard, Jobs, Screening, Interviews, Interview Marks, Selected Candidates, Settings, Reports

### 3. Interviewer Portal (External)
- **URL:** Shared link from HR, e.g. `/interviewer/join/<token>`
- **Who:** External interview panel members (no personal password)
- **Access:** Name + shared 8-digit panel access code
- **Purpose:** Score shortlisted candidates for assigned job

### 4. Audit Portal
- **URL:** `/login` → `/audit`
- **Who:** Audit managers and audit members
- **Purpose:** Review system activity and compliance

---

## Main Features

### Recruitment
- Create and manage job postings (`positions_needed` per job)
- Public careers page with search and filters
- One application per email per job (duplicate prevention)
- CV upload (PDF, DOCX) with automatic scoring

### Screening
- AI-assisted CV ranking (TF-IDF + skill matching)
- Manual screening with notes
- Reject candidates with optional email

### Interviews
- Schedule interviews with date, time, type, location
- Personalized email invitations (HTML with company logo)
- Interview status tracking: scheduled → in progress → completed
- **Interview Marks** table with criteria: presentation, dressing, communication, confidence, technical knowledge, problem solving, attitude

### External Interviewers
- Add multiple interviewers per job
- Generate **one shared link** + **one access code** (24-hour expiry)
- Interviewers sign in and submit scores; marks appear in HR Interview Marks

### Communication
- SMTP email for interviews, rejections, bulk messages
- Email history log
- Company logo embedded in outgoing emails

### Settings & Branding
- Company name, logo, welcome image, welcome video
- Mail server configuration and test email
- User and permission management

---

## Project Structure

```
hr/
├── app.py                    # Main Flask application (routes, logic, data loading)
├── requirements.txt          # Python dependencies
├── .env                      # Local secrets (do NOT commit)
├── .env.example              # Example environment variables
│
├── data/                     # JSON database (auto-created)
│   ├── users.json            # All user accounts
│   ├── jobs.json             # Job postings
│   ├── applications.json     # Candidate applications
│   ├── settings.json         # Company branding & mail settings
│   ├── interviewer_panels.json
│   ├── activity_logs.json
│   └── email_history.json
│
├── static/                   # Public static files (CSS, default logo)
│   ├── style.css
│   └── gmb-logo.svg          # Default logo if none uploaded in Settings
│
├── uploads/                  # User-uploaded files
│   ├── branding/             # Company logo, welcome video
│   │   ├── company_logo.png
│   │   └── welcome-video.mp4
│   └── <uuid>_cv_*.pdf       # Applicant CVs (auto-saved on apply)
│
├── templates/                # HTML pages
│   ├── index.html            # Applicant job listings
│   ├── apply.html            # Application form
│   ├── login.html            # HR / Audit login
│   ├── hr_dashboard.html     # Main HR dashboard
│   ├── interviewer_join.html # Interviewer sign-in
│   └── interviewer_dashboard.html
│
├── services/                 # Business logic modules
│   ├── cv_scoring.py         # CV parsing and ranking
│   ├── document_validation.py
│   └── email_service.py
│
└── docs/                     # Project documentation assets
    └── images/               # Screenshots & diagrams for documentation
```

---

## Where to Put Pictures & Media

This is the most important section for customizing visuals.

### A. Company Logo (Recommended: HR Settings upload)

| Use | Where it appears |
|-----|------------------|
| HR login page | `templates/login.html` |
| HR dashboard sidebar | `templates/hr_dashboard.html` |
| Interviewer portal | `templates/interviewer_join.html`, `interviewer_dashboard.html` |
| Applicant portal header | `templates/index.html` |
| Outgoing emails | Embedded as `cid:company_logo` |

**Best method:** Upload in **HR → Settings → Portal Branding** (no code change needed).

**File saved to:** `uploads/branding/company_logo.png` (or `.jpg`)

**Fallback default:** `static/gmb-logo.svg` — replace this file if you want a default logo before uploading in Settings.

**Supported formats:** PNG, JPG, SVG (via Settings upload)

---

### B. Applicant Portal Welcome Image

**Purpose:** Hero/banner image on the applicant landing page.

**Best method:** Upload in **HR → Settings → Portal Branding** as “Welcome Image”.

**Stored in:** `data/settings.json` (base64) — managed automatically by the app.

**Alternative (manual):** Place an image in `static/` and reference it in `templates/index.html`:

```html
<img src="{{ url_for('static', filename='your-welcome-image.jpg') }}" alt="Welcome">
```

Suggested path: `static/images/welcome-banner.jpg`

---

### C. Applicant Portal Welcome Video

**Purpose:** Company intro video on the applicant homepage.

**Best method:** Upload in **HR → Settings → Portal Branding** as “Welcome Video”.

**File saved to:** `uploads/branding/<your-video-name>.mp4`

**Served at:** `/portal/branding/<filename>`

**Tips:**
- Use MP4 (H.264) for best browser compatibility
- Keep file size reasonable (under 50 MB if possible)
- See also: `WELCOME_VIDEO_SETUP.md`

---

### D. Applicant CVs & Certificates (Automatic)

When candidates apply, files are saved automatically:

```
uploads/
  <application-id>_cv_<filename>.pdf
  <application-id>_cert_<index>_<filename>.pdf
```

**Do not place these manually** — the apply form handles uploads.

---

### E. Static UI Assets (CSS, icons, default graphics)

| Folder | Use |
|--------|-----|
| `static/` | CSS, default logo, any fixed images used in templates |
| `static/images/` | Create this folder for extra UI images (banners, icons) |

Example structure:

```
static/
├── style.css
├── gmb-logo.svg
└── images/
    ├── hero-banner.jpg
    ├── favicon.ico
    └── team-photo.png
```

Reference in templates:

```html
<img src="{{ url_for('static', filename='images/hero-banner.jpg') }}" alt="Our team">
```

---

### F. Documentation Screenshots (For your project report/presentation)

Create screenshots of the running app and save them here:

```
docs/images/
├── 01-applicant-portal.png
├── 02-hr-dashboard.png
├── 03-interview-marks.png
├── 04-interviewer-portal.png
└── 05-settings-branding.png
```

These are **not used by the app** — they are for your documentation, reports, or presentations only.

---

### Quick Reference: Where to Put What

| What you want | Where to put it | How to activate |
|---------------|-----------------|-----------------|
| Company logo | HR Settings upload **or** `static/gmb-logo.svg` | Settings → Portal Branding |
| Welcome banner image | HR Settings **or** `static/images/` | Settings or edit `index.html` |
| Welcome video | `uploads/branding/` via Settings | Settings → Portal Branding |
| Applicant CVs | `uploads/` (automatic) | Candidate applies online |
| CSS / styling | `static/style.css` | Edit file directly |
| Doc screenshots | `docs/images/` | Manual — for reports only |

---

## Installation & Running

### Prerequisites
- Python 3.11+
- pip

### Steps (Windows)

```powershell
cd C:\Users\PC\hr
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open: **http://localhost:5000**

### Health check
```
GET http://localhost:5000/health
```

---

## Configuration

### Environment variables (`.env`)

Create a `.env` file in the project root (copy from `.env.example`):

```env
SECRET_KEY=your-secret-key-here

# Email (SMTP)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833), not your normal login password.

### Settings saved in app
Most branding and mail options are also stored in `data/settings.json` and can be changed from **HR → Settings** without editing files.

---

## Default Logins

| Role | Email | Password |
|------|-------|----------|
| HR Manager | `hr@company.com` | `password123` |
| Audit Manager | `audit@company.com` | `password123` |

**Interviewer access:** No fixed login — HR generates a shared link + 8-digit access code per job panel.

> Change default passwords before deploying to production.

---

## Typical Workflows

### HR: Full hiring flow

1. **Login** at `/login`
2. **Post a job** — HR Dashboard → Jobs (set positions needed)
3. **Wait for applications** — candidates apply via `/portal`
4. **Screen candidates** — Screening section, run CV scoring
5. **Schedule interviews** — Interviews section, send email invite
6. **Add external interviewers** (optional):
   - Interviews → External Interviewer Setup
   - Add names/emails → Generate Shared Link
   - Share link + access code with panel
7. **Review marks** — Interview Marks section
8. **Select candidates** — Selected Candidates section

### Interviewer: Score candidates

1. Open shared link from HR
2. Enter **full name** (as registered) + **panel access code**
3. Evaluate candidates and submit scores
4. Scores appear in HR Interview Marks

### Applicant: Apply for a job

1. Visit `/` or `/portal`
2. Browse/search jobs
3. Click **Apply** → fill form → upload CV
4. Confirmation on success page

---

## Data Storage

The app uses **JSON files** in `data/` as its primary database. Files are loaded into memory on startup and saved when changes occur.

| File | Contents |
|------|----------|
| `users.json` | HR, audit, interviewer accounts |
| `jobs.json` | Job postings |
| `applications.json` | All candidate applications and interview data |
| `settings.json` | Company name, logo (base64), mail config |
| `interviewer_panels.json` | Shared links, access codes, panel members |
| `activity_logs.json` | Audit trail of user actions |
| `email_history.json` | Sent email log |

**Backup tip:** Copy the entire `data/` and `uploads/` folders regularly.

---

## API & Key Routes

| Route | Description |
|-------|-------------|
| `/` | Applicant job listings |
| `/login` | HR / Audit login |
| `/hr` | HR dashboard |
| `/jobs/<id>/apply` | Application form |
| `/hr/jobs/post` | Create job (POST) |
| `/hr/applications/<id>/screen` | Screen candidate |
| `/hr/interviews/schedule` | Schedule interview |
| `/hr/interviewers/add` | Add external interviewer |
| `/hr/interviewers/generate-link` | Generate panel link + code |
| `/interviewer/join/<token>` | Interviewer sign-in |
| `/interviewer/dashboard` | Interviewer scoring portal |
| `/hr/settings/portal-branding` | Upload logo, image, video |
| `/portal/branding/<file>` | Serve branding video/files |
| `/uploads/<file>` | Serve uploaded CVs |

---

## Branding & Colors

Project color palette (used across HR and interviewer portals):

| Color | Hex | Usage |
|-------|-----|-------|
| Teal | `#124e66` | Headers, primary brand |
| Dark navy | `#0a2338` | Gradients, sidebar |
| Orange | `#f39c12` | Buttons, accents, highlights |
| Orange dark | `#e67e22` | Button hover |
| Light gray | `#f5f7fa` | Page backgrounds |

Main stylesheet: `static/style.css`

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| App won't start | Check Python version, run `pip install -r requirements.txt` |
| Emails not sending | Configure SMTP in `.env` or HR Settings; test with Settings → Test Email |
| Logo not showing | Upload in HR Settings, or place file at `static/gmb-logo.svg` |
| Welcome video not playing | Use MP4 in `uploads/branding/`; upload via Settings |
| Interviewer link expired | HR must generate a new link (valid 24 hours) |
| Wrong access code | Use the code shown when HR generated the link |
| Duplicate application | Same email cannot apply twice to the same job |

---

## Related Documentation Files

| File | Topic |
|------|-------|
| `README.md` | Quick start and feature list |
| `QUICK_START.md` | Short setup guide |
| `SETUP_GUIDE.md` | Detailed setup |
| `WELCOME_VIDEO_SETUP.md` | Welcome video customization |
| `APPLICANT_PORTAL_CHANGES.md` | Applicant portal updates |
| `DEPLOYMENT_CHECKLIST.md` | Production deployment |

---

## Support

- **Company settings:** HR → Settings in the dashboard
- **Technical issues:** Check `data/activity_logs.json` for recent actions
- **Email problems:** Verify `.env` SMTP credentials and test from Settings

---

*Last updated: June 2026*
