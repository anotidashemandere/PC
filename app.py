#!/usr/bin/env python
"""HR System Flask Application"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timezone, timedelta
from pathlib import Path
from email.message import EmailMessage
import json
import os
import smtplib

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-12345")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
app.config["SESSION_COOKIE_HTTPONLY"] = True

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# In-memory storage
USERS = {}
JOBS = {}
APPLICATIONS = {}
ACTIVITY_LOGS = []
SETTINGS = {}

DEFAULT_SETTINGS = {
    "company_name": "GMB",
    "support_email": "hr@company.com",
    "default_view": "dashboard",
    "items_per_page": 25,
    "notification_email_enabled": True,
    "application_updates_enabled": True,
    "interview_reminders_enabled": True,
    "weekly_reports_enabled": False,
    "mail_server": os.environ.get("MAIL_SERVER", "smtp.gmail.com"),
    "mail_port": int(os.environ.get("MAIL_PORT", 587)),
    "mail_use_tls": str(os.environ.get("MAIL_USE_TLS", "true")).lower() in ("1", "true", "yes", "on"),
    "mail_username": os.environ.get("MAIL_USERNAME", ""),
    "mail_password": os.environ.get("MAIL_PASSWORD", ""),
    "mail_default_sender": os.environ.get("MAIL_DEFAULT_SENDER", os.environ.get("MAIL_USERNAME", "noreply@company.com")),
    "interview_default_message": (
        "Dear {candidate_name},\n\n"
        "You are invited to an interview for the {job_title} role on {interview_date} at {interview_time}.\n"
        "Interview type: {interview_type}.\n"
        "Location/Link: {interview_location}.\n\n"
        "Regards,\nHR Team"
    ),
}


def _settings_file():
    return DATA_DIR / "settings.json"


def _save_json(path, payload):
    with open(path, "w") as file_obj:
        json.dump(payload, file_obj, indent=2, default=str)


def _to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _normalize_requirements(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _parse_iso_datetime(value):
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value:
        try:
            parsed = datetime.fromisoformat(value)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def _screening_text_for_job(job):
    requirements = _normalize_requirements(job.get("requirements"))
    custom_criteria = (job.get("screening_criteria") or job.get("custom_screening_criteria") or "").strip()
    parts = [
        job.get("title", ""),
        job.get("description", ""),
        f"Requirements: {', '.join(requirements)}" if requirements else "",
        custom_criteria,
    ]
    return "\n".join(part for part in parts if part)


def _normalize_screening_status(raw_status):
    status = str(raw_status or "pending").strip().lower()
    status_map = {
        "shortlisted": "shortlisted",
        "review": "pending",
        "pending review": "pending",
        "interview": "interview",
        "rejected": "rejected",
    }
    return status_map.get(status, status or "pending")


def _screen_pending_applications(job_ids, trigger="manual"):
    try:
        from services.cv_scoring import ResumeUpload, rank_candidates
    except Exception as exc:
        print(f"Warning: CV scoring service unavailable: {exc}")
        return {"processed": 0, "jobs": []}

    processed = 0
    touched_jobs = []

    for job_id in job_ids:
        job = JOBS.get(job_id)
        if not job:
            continue

        screening_text = _screening_text_for_job(job)
        if not screening_text.strip():
            continue

        job_processed = 0
        for app_data in APPLICATIONS.values():
            if app_data.get("job_id") != job_id:
                continue
            if str(app_data.get("status") or "pending").strip().lower() != "pending":
                continue

            resume_path = Path(app_data.get("resume_path") or "")
            if not resume_path.exists():
                continue

            try:
                result = rank_candidates(
                    screening_text,
                    [ResumeUpload(label=app_data.get("id", "candidate"), path=resume_path)],
                )[0]
            except Exception as exc:
                print(f"Warning: Could not screen application {app_data.get('id')}: {exc}")
                continue

            app_data["score"] = result.score
            app_data["summary"] = result.summary
            app_data["recommendation"] = result.recommendation
            app_data["recommendation_reason"] = result.recommendation_reason
            app_data["matched_skills"] = result.matched_skills
            app_data["missing_skills"] = result.missing_skills
            app_data["status"] = _normalize_screening_status(result.status)
            app_data["screened_at"] = datetime.now(timezone.utc).isoformat()
            app_data["screening_trigger"] = trigger
            job_processed += 1
            processed += 1

        if job_processed:
            touched_jobs.append({"job_id": job_id, "job_title": job.get("title", "Job"), "processed": job_processed})

    if processed:
        save_applications()

    return {"processed": processed, "jobs": touched_jobs}


def _screen_due_jobs():
    now = datetime.now(timezone.utc)
    due_job_ids = []
    for job_id, job in JOBS.items():
        due_date = _parse_iso_datetime(job.get("due_date"))
        if due_date and due_date <= now:
            due_job_ids.append(job_id)
    return _screen_pending_applications(due_job_ids, trigger="due_date") if due_job_ids else {"processed": 0, "jobs": []}


def save_jobs():
    _save_json(DATA_DIR / "jobs.json", JOBS)


def save_applications():
    _save_json(DATA_DIR / "applications.json", APPLICATIONS)


def save_settings():
    _save_json(_settings_file(), SETTINGS)


def _mail_settings():
    return {
        "server": SETTINGS.get("mail_server") or DEFAULT_SETTINGS["mail_server"],
        "port": int(SETTINGS.get("mail_port") or DEFAULT_SETTINGS["mail_port"]),
        "use_tls": _to_bool(SETTINGS.get("mail_use_tls", DEFAULT_SETTINGS["mail_use_tls"])),
        "username": SETTINGS.get("mail_username") or DEFAULT_SETTINGS["mail_username"],
        "password": SETTINGS.get("mail_password") or DEFAULT_SETTINGS["mail_password"],
        "sender": SETTINGS.get("mail_default_sender") or DEFAULT_SETTINGS["mail_default_sender"],
    }


def send_email_message(recipient, subject, body):
    if not recipient:
        return False, "Candidate email is missing"

    mail = _mail_settings()
    if not mail["server"] or not mail["port"] or not mail["sender"]:
        return False, "SMTP settings are incomplete"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = mail["sender"]
    message["To"] = recipient
    message.set_content(body)

    try:
        with smtplib.SMTP(mail["server"], mail["port"], timeout=20) as smtp:
            if mail["use_tls"]:
                smtp.starttls()
            if mail["username"]:
                smtp.login(mail["username"], mail["password"])
            smtp.send_message(message)
        return True, None
    except Exception as exc:
        print(f"Warning: Could not send email: {exc}")
        return False, str(exc)


def load_all_data():
    """Load all data from disk"""
    # Load users
    users_file = DATA_DIR / "users.json"
    if users_file.exists():
        try:
            with open(users_file, 'r') as f:
                USERS.update(json.load(f))
        except Exception as e:
            print(f"Warning: Could not load users: {e}")

    # Ensure default users exist
    if not USERS:
        USERS["user-001"] = {
            "id": "user-001",
            "email": "hr@company.com",
            "name": "HR Manager",
            "password_hash": generate_password_hash("password123"),
            "role": "hr"
        }
        USERS["user-002"] = {
            "id": "user-002",
            "email": "audit@company.com",
            "name": "Audit Manager",
            "password_hash": generate_password_hash("password123"),
            "role": "audit"
        }
        try:
            with open(users_file, 'w') as f:
                json.dump(USERS, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save default users: {e}")

    # Load jobs
    jobs_file = DATA_DIR / "jobs.json"
    if jobs_file.exists():
        try:
            with open(jobs_file, 'r') as f:
                JOBS.update(json.load(f))
        except Exception as e:
            print(f"Warning: Could not load jobs: {e}")

    # Load applications
    apps_file = DATA_DIR / "applications.json"
    if apps_file.exists():
        try:
            with open(apps_file, 'r') as f:
                APPLICATIONS.update(json.load(f))
        except Exception as e:
            print(f"Warning: Could not load applications: {e}")

    # Load activity logs
    logs_file = DATA_DIR / "activity_logs.json"
    if logs_file.exists():
        try:
            with open(logs_file, 'r') as f:
                for entry in json.load(f):
                    if isinstance(entry.get('timestamp'), str):
                        try:
                            entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                        except Exception:
                            entry['timestamp'] = datetime.now(timezone.utc)
                    ACTIVITY_LOGS.append(entry)
        except Exception as e:
            print(f"Warning: Could not load activity logs: {e}")

    settings_file = _settings_file()
    SETTINGS.update(DEFAULT_SETTINGS)
    if settings_file.exists():
        try:
            with open(settings_file, 'r') as f:
                SETTINGS.update(json.load(f))
        except Exception as e:
            print(f"Warning: Could not load settings: {e}")


load_all_data()


def log_activity(user_id, action, details="", status="success"):
    """Append an activity log entry and persist it."""
    entry = {
        "user_id": user_id,
        "action": action,
        "details": details,
        "status": status,
        "timestamp": datetime.now(timezone.utc),
    }
    ACTIVITY_LOGS.append(entry)
    try:
        serializable = []
        for e in ACTIVITY_LOGS[-1000:]:
            ec = dict(e)
            if isinstance(ec.get('timestamp'), datetime):
                ec['timestamp'] = ec['timestamp'].isoformat()
            serializable.append(ec)
        with open(DATA_DIR / "activity_logs.json", 'w') as f:
            json.dump(serializable, f, indent=2)
    except Exception as ex:
        print(f"Warning: Could not save activity logs: {ex}")


def get_current_user():
    """Get currently logged-in user"""
    if "user_id" in session:
        return USERS.get(session["user_id"])
    return None


@app.context_processor
def inject_user():
    return {'current_user': get_current_user()}


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "users": len(USERS),
        "jobs": len(JOBS),
        "applications": len(APPLICATIONS),
        "logs": len(ACTIVITY_LOGS),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.route("/")
def index():
    user = get_current_user()
    if user:
        if user.get("role") == "audit":
            return redirect(url_for("audit_dashboard"))
        return redirect(url_for("hr_dashboard"))
    jobs = [_wrap_job(j) for j in JOBS.values()]
    return render_template("index.html", jobs=jobs)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        user = None
        for u in USERS.values():
            if u.get("email", "").lower() == email:
                user = u
                break

        if user and check_password_hash(user.get("password_hash", ""), password):
            session.permanent = True
            session["user_id"] = user["id"]
            log_activity(user["id"], "login", f"User {user.get('email')} logged in", "success")
            if user.get("role") == "audit":
                return redirect(url_for("audit_dashboard"))
            return redirect(url_for("hr_dashboard"))
        else:
            uid = user["id"] if user else "unknown"
            log_activity(uid, "login_failed", f"Failed login for {email}", "failed")
            flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    user = get_current_user()
    if user:
        log_activity(user["id"], "logout", f"User {user.get('email')} logged out", "success")
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/hr")
def hr_dashboard():
    user = get_current_user()
    if not user:
        flash("Please log in.", "warning")
        return redirect(url_for("login"))
    if user.get("role") != "hr":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    _screen_due_jobs()

    dashboards = []
    for job_id, job in JOBS.items():
        applicants = [_enrich_application(a) for a in APPLICATIONS.values() if a.get("job_id") == job_id]
        enriched_job = _enrich_job(job)
        # Convert uploaded_at strings to datetime objects
        for a in applicants:
            if isinstance(a.get("uploaded_at"), str):
                try:
                    a["uploaded_at"] = datetime.fromisoformat(a["uploaded_at"])
                except Exception:
                    a["uploaded_at"] = datetime.now(timezone.utc)
        dashboards.append({
            "job": enriched_job,
            "applicants": applicants,
            "applicant_count": len(applicants),
            "all_count": len(applicants),
            "selected_count": len([a for a in applicants if a.get("status") == "shortlisted"]),
            "deadline_state": enriched_job.get("deadline_state", "open"),
        })

    all_applicants_data = [_enrich_application(app_data) for app_data in APPLICATIONS.values()]
    # Convert uploaded_at strings to datetime objects
    for a in all_applicants_data:
        if isinstance(a.get("uploaded_at"), str):
            try:
                a["uploaded_at"] = datetime.fromisoformat(a["uploaded_at"])
            except Exception:
                a["uploaded_at"] = datetime.now(timezone.utc)
    return render_template(
        "hr_dashboard.html",
        dashboards=dashboards,
        applicants=all_applicants_data,
        all_applicants=all_applicants_data,
        interviews=_scheduled_interviews(),
        settings=SETTINGS,
    )


@app.route("/audit")
def audit_dashboard():
    user = get_current_user()
    if not user:
        flash("Please log in.", "warning")
        return redirect(url_for("login"))
    if user.get("role") not in ("audit", "hr"):
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    PER_PAGE = 25
    page = max(1, request.args.get("page", 1, type=int))
    action_filter = request.args.get("action", "").strip().lower()

    def _normalize_log(entry):
        item = dict(entry or {})
        ts = item.get("timestamp")
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts)
            except Exception:
                ts = datetime.now(timezone.utc)
        if not isinstance(ts, datetime):
            ts = datetime.now(timezone.utc)

        user_ref = USERS.get(item.get("user_id"), {})
        item["timestamp"] = ts
        item["created_at"] = ts
        item["user"] = {
            "full_name": user_ref.get("name") or item.get("user_id") or "Unknown User",
            "email": user_ref.get("email") or "unknown@local",
        }
        return item

    # Sort newest first
    all_logs = sorted([_normalize_log(log) for log in ACTIVITY_LOGS], key=lambda x: x.get("timestamp"), reverse=True)

    filtered = [l for l in all_logs if action_filter in l.get("action", "").lower()] if action_filter else all_logs

    total_logs = len(all_logs)
    successful_count = sum(1 for l in all_logs if l.get("status") == "success")
    failed_count = sum(1 for l in all_logs if l.get("status") != "success")
    unique_users = len(set(l.get("user_id") for l in all_logs if l.get("user_id")))

    login_logs = [l for l in all_logs if l.get("action") in ("login", "logout")][:20]

    total_pages = max(1, (len(filtered) + PER_PAGE - 1) // PER_PAGE)
    page = min(page, total_pages)
    logs = filtered[(page - 1) * PER_PAGE: page * PER_PAGE]

    return render_template(
        "audit_dashboard.html",
        logs=logs,
        login_logs=login_logs,
        login_activities=login_logs,
        total_logs=total_logs,
        successful_count=successful_count,
        failed_count=failed_count,
        unique_users=unique_users,
        page=page,
        current_page=page,
        total_pages=total_pages,
        action_filter=action_filter,
    )


# ─── Helper: dict wrapper for attribute access in templates ───────────────
class _DictObj:
    """Wrap a plain dict so Jinja2 can access fields as attributes,
    with special handling for file paths and datetimes."""
    def __init__(self, d):
        object.__setattr__(self, '_d', d or {})

    def __getattr__(self, name):
        d = object.__getattribute__(self, '_d')
        val = d.get(name)
        if name == 'resume_path' and val:
            return Path(val)
        if name == 'certification_paths':
            return [Path(p) for p in (val or [])]
        if name == 'uploaded_at' and isinstance(val, str):
            try:
                return datetime.fromisoformat(val)
            except Exception:
                return datetime.now(timezone.utc)
        if name in ('due_date', 'interview_at') and isinstance(val, str):
            parsed = _parse_iso_datetime(val)
            if parsed:
                return parsed
        if name == 'requirements':
            return _normalize_requirements(val)
        return val

    def __getitem__(self, key):
        return object.__getattribute__(self, '_d').get(key)

    def __bool__(self):
        return bool(object.__getattribute__(self, '_d'))

    def get(self, key, default=None):
        """Dict-like get method"""
        return object.__getattribute__(self, '_d').get(key, default)


class _AppObj(_DictObj):
    @property
    def job_ref(self):
        job = JOBS.get(object.__getattribute__(self, '_d').get('job_id', ''))
        return _DictObj(job) if job else None


def _wrap_app(d):
    return _AppObj(d)


def _wrap_job(d):
    return _DictObj(d)


def _enrich_job(job):
    item = dict(job or {})
    item["requirements"] = _normalize_requirements(item.get("requirements"))
    due_date = _parse_iso_datetime(item.get("due_date"))
    item["due_date"] = due_date.isoformat() if due_date else item.get("due_date")
    item["application_link"] = item.get("application_link") or url_for("apply", job_id=item.get("id", ""))
    item["deadline_state"] = "closed" if due_date and due_date < datetime.now(timezone.utc) else "open"
    return item


def _enrich_application(app_data):
    item = dict(app_data or {})
    job = JOBS.get(item.get("job_id", ""), {})
    item["job_title"] = job.get("title") or "General Application"
    job_due_date = _parse_iso_datetime(job.get("due_date"))
    item["job_due_date"] = job_due_date.isoformat() if job_due_date else ""
    item["job_deadline_state"] = "closed" if job_due_date and job_due_date <= datetime.now(timezone.utc) else "open"
    interview_date = (item.get("interview_date") or "").strip()
    interview_time = (item.get("interview_time") or "").strip()
    if interview_date and interview_time:
        item["interview_at"] = f"{interview_date}T{interview_time}"
    elif interview_date:
        item["interview_at"] = interview_date
    return item


def _scheduled_interviews():
    interviews = []
    for app_data in APPLICATIONS.values():
        if app_data.get("interview_date"):
            enriched = _enrich_application(app_data)
            # Ensure interview_at is a datetime object
            if isinstance(enriched.get("interview_at"), str):
                try:
                    enriched["interview_at"] = datetime.fromisoformat(enriched["interview_at"])
                except Exception:
                    pass
            interviews.append(enriched)
    interviews.sort(key=lambda item: (item.get("interview_date", ""), item.get("interview_time", "")))
    return interviews


def _require_hr():
    user = get_current_user()
    if not user:
        flash("Please log in.", "warning")
        return None, redirect(url_for("login"))
    if user.get("role") != "hr":
        flash("Access denied.", "danger")
        return None, redirect(url_for("login"))
    return user, None


# ─── HR sub-pages ──────────────────────────────────────────────────────────
@app.route("/hr/jobs", methods=["GET"])
def hr_jobs():
    user, err = _require_hr()
    if err:
        return err
    _screen_due_jobs()
    jobs = [_wrap_job(_enrich_job(j)) for j in JOBS.values()]
    return render_template("hr_jobs.html", jobs=jobs)


@app.route("/hr/jobs/post", methods=["POST"])
def hr_post_job():
    user, err = _require_hr()
    if err:
        return err
    import uuid
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "id": job_id,
        "title": request.form.get("title", "").strip(),
        "department": request.form.get("department", "").strip(),
        "location": request.form.get("location", "").strip(),
        "description": request.form.get("description", "").strip(),
        "requirements": _normalize_requirements(request.form.get("requirements", "")),
        "screening_criteria": request.form.get("screening_criteria", "").strip(),
        "due_date": request.form.get("due_date", "").strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "application_link": url_for("apply", job_id=job_id),
    }
    try:
        save_jobs()
    except Exception as e:
        print(f"Warning: Could not save job: {e}")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True, "job": _enrich_job(JOBS[job_id])})
    flash("Job posted successfully.", "success")
    return redirect(url_for("hr_jobs"))


@app.route("/hr/screening")
def hr_screening():
    user, err = _require_hr()
    if err:
        return err
    screening_summary = _screen_due_jobs()
    all_apps = [_wrap_app(_enrich_application(a)) for a in APPLICATIONS.values()]
    pending = [a for a in all_apps if not a.status or a.status == "pending"]
    shortlisted = [a for a in all_apps if a.status == "shortlisted"]
    rejected = [a for a in all_apps if a.status == "rejected"]
    return render_template(
        "hr_screening.html",
        applicants=all_apps,
        pending=pending,
        shortlisted=shortlisted,
        rejected=rejected,
        screening_summary=screening_summary,
    )


@app.route("/hr/screening/run-now", methods=["POST"])
def hr_screening_run_now():
    user, err = _require_hr()
    if err:
        return err
    summary = _screen_pending_applications(list(JOBS.keys()), trigger="manual")
    log_activity(user["id"], "screen_due_candidates", f"Processed {summary['processed']} candidate(s)", "success")
    return jsonify({"ok": True, **summary})


@app.route("/hr/interviews")
def hr_interviews():
    user, err = _require_hr()
    if err:
        return err
    applicants = [_wrap_app(_enrich_application(a)) for a in _scheduled_interviews()]
    candidates = [_wrap_app(_enrich_application(a)) for a in APPLICATIONS.values() if a.get("status") in ("shortlisted", "interview", "pending")]
    return render_template("hr_interviews.html", applicants=applicants, candidates=candidates, settings=SETTINGS)


@app.route("/hr/ratings")
def hr_ratings():
    user, err = _require_hr()
    if err:
        return err
    applicants = [_wrap_app(a) for a in APPLICATIONS.values()]
    return render_template("hr_ratings.html", applicants=applicants)


@app.route("/hr/settings", methods=["GET"])
def hr_settings():
    user, err = _require_hr()
    if err:
        return err
    return render_template("hr_settings.html", settings=SETTINGS)


@app.route("/hr/settings/update", methods=["POST"])
def hr_settings_update():
    user, err = _require_hr()
    if err:
        return err
    SETTINGS.update({
        "company_name": request.form.get("company_name", SETTINGS.get("company_name", DEFAULT_SETTINGS["company_name"])).strip(),
        "support_email": request.form.get("support_email", SETTINGS.get("support_email", DEFAULT_SETTINGS["support_email"])).strip(),
        "default_view": request.form.get("default_view", SETTINGS.get("default_view", DEFAULT_SETTINGS["default_view"])).strip(),
        "items_per_page": int(request.form.get("items_per_page", SETTINGS.get("items_per_page", DEFAULT_SETTINGS["items_per_page"]))),
        "notification_email_enabled": "notification_email_enabled" in request.form,
        "application_updates_enabled": "application_updates_enabled" in request.form,
        "interview_reminders_enabled": "interview_reminders_enabled" in request.form,
        "weekly_reports_enabled": "weekly_reports_enabled" in request.form,
    })
    save_settings()
    flash("Settings saved.", "success")
    return redirect(url_for("hr_settings"))


@app.route("/hr/applications/<application_id>")
def hr_application_detail(application_id):
    user, err = _require_hr()
    if err:
        return err
    app_data = APPLICATIONS.get(application_id)
    if not app_data:
        flash("Application not found.", "danger")
        return redirect(url_for("hr_screening"))
    application = _wrap_app(app_data)
    job = _wrap_job(JOBS.get(app_data.get("job_id", "")) or {})
    return render_template("application_detail.html", application=application, job=job)


@app.route("/hr/applications/<application_id>/action", methods=["POST"])
def hr_application_action(application_id):
    user, err = _require_hr()
    if err:
        return err
    action = request.form.get("action", "")
    if application_id in APPLICATIONS:
        APPLICATIONS[application_id]["status"] = action
        try:
            with open(DATA_DIR / "applications.json", "w") as f:
                json.dump(APPLICATIONS, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save applications: {e}")
        flash(f"Application marked as {action}.", "success")
    return redirect(url_for("hr_application_detail", application_id=application_id))


@app.route("/hr/applications/<application_id>/screen", methods=["POST"])
def hr_application_screen(application_id):
    user, err = _require_hr()
    if err:
        return err

    app_data = APPLICATIONS.get(application_id)
    if not app_data:
        return jsonify({"ok": False, "error": "Application not found"}), 404

    payload = request.get_json(silent=True) or request.form
    raw_status = (payload.get("status") or "pending").strip().lower()
    status_map = {
        "shortlisted": "shortlisted",
        "pending review": "pending",
        "pending": "pending",
        "rejected": "rejected",
        "interview ready": "interview",
        "interview": "interview",
    }
    app_data["status"] = status_map.get(raw_status, raw_status or "pending")
    app_data["screening_rating"] = payload.get("rating")
    app_data["screening_notes"] = (payload.get("notes") or "").strip()
    app_data["screened_at"] = datetime.now(timezone.utc).isoformat()
    save_applications()
    log_activity(user["id"], "screen_candidate", f"Screened {application_id}", "success")
    return jsonify({"ok": True, "status": app_data["status"]})


@app.route("/hr/applications/<application_id>/reject", methods=["POST"])
def hr_application_reject(application_id):
    user, err = _require_hr()
    if err:
        return err

    app_data = APPLICATIONS.get(application_id)
    if not app_data:
        return jsonify({"ok": False, "error": "Application not found"}), 404

    payload = request.get_json(silent=True) or request.form
    send_email = _to_bool(payload.get("send_email", False))
    app_data["status"] = "rejected"
    app_data["rejection_reason"] = (payload.get("reason") or "").strip()
    app_data["rejection_message"] = (payload.get("message") or "").strip()
    app_data["rejected_at"] = datetime.now(timezone.utc).isoformat()

    email_result = None
    if send_email and app_data.get("email"):
        subject = f"Application Update - {app_data.get('name', 'Candidate')}"
        body = app_data["rejection_message"] or "Thank you for your application. We will not move forward at this time."
        sent, error = send_email_message(app_data.get("email"), subject, body)
        email_result = {"sent": sent, "error": error}
        app_data["rejection_email_sent"] = sent

    save_applications()
    log_activity(user["id"], "reject_candidate", f"Rejected {application_id}", "success")
    return jsonify({"ok": True, "email": email_result})


@app.route("/hr/interviews/schedule", methods=["POST"])
def hr_schedule_interview():
    user, err = _require_hr()
    if err:
        return err

    payload = request.get_json(silent=True) or request.form
    application_id = (payload.get("application_id") or "").strip()
    app_data = APPLICATIONS.get(application_id)
    if not app_data:
        return jsonify({"ok": False, "error": "Application not found"}), 404

    interview_date = (payload.get("interview_date") or "").strip()
    interview_time = (payload.get("interview_time") or "").strip()
    if not interview_date or not interview_time:
        return jsonify({"ok": False, "error": "Interview date and time are required"}), 400

    app_data["status"] = "interview"
    app_data["interview_date"] = interview_date
    app_data["interview_time"] = interview_time
    app_data["interview_type"] = (payload.get("interview_type") or "Interview").strip()
    app_data["interviewer"] = (payload.get("interviewer") or "").strip()
    app_data["interview_location"] = (payload.get("interview_location") or "").strip()
    app_data["interview_message"] = (payload.get("message") or "").strip()
    app_data["interview_status"] = "scheduled"
    app_data["interview_scheduled_at"] = datetime.now(timezone.utc).isoformat()

    email_result = None
    send_email = _to_bool(payload.get("send_email", False))
    if send_email and app_data.get("email"):
        job = JOBS.get(app_data.get("job_id", ""), {})
        template = app_data["interview_message"] or SETTINGS.get("interview_default_message", DEFAULT_SETTINGS["interview_default_message"])
        format_values = {
            "candidate_name": f"{app_data.get('name', '')} {app_data.get('surname', '')}".strip(),
            "job_title": job.get("title", "the position"),
            "interview_date": interview_date,
            "interview_time": interview_time,
            "interview_type": app_data.get("interview_type", "Interview"),
            "interview_location": app_data.get("interview_location", "To be confirmed"),
        }
        try:
            body = template.format(**format_values)
        except Exception:
            body = template
        if interview_date not in body or interview_time not in body:
            body = (
                f"{body}\n\nInterview schedule:\n"
                f"Date: {interview_date}\n"
                f"Time: {interview_time}\n"
                f"Type: {format_values['interview_type']}\n"
                f"Location/Link: {format_values['interview_location']}"
            )
        subject = f"Interview Invitation - {job.get('title', 'Application')}"
        sent, error = send_email_message(app_data.get("email"), subject, body)
        email_result = {"sent": sent, "error": error}
        app_data["interview_email_sent"] = sent
        app_data["interview_email_error"] = error

    save_applications()
    log_activity(user["id"], "schedule_interview", f"Scheduled interview for {application_id}", "success")
    return jsonify({"ok": True, "email": email_result, "application": _enrich_application(app_data)})


@app.route("/applicants/<application_id>")
def applicant_page(application_id):
    app_data = APPLICATIONS.get(application_id)
    if not app_data:
        flash("Application not found.", "danger")
        return redirect(url_for("index"))
    application = _wrap_app(app_data)
    job = _wrap_job(JOBS.get(app_data.get("job_id", "")) or {})
    return render_template("applicant_page.html", application=application, job=job)


@app.route("/hr/report")
def hr_report_summary():
    user, err = _require_hr()
    if err:
        return err
    import csv, io

    status_filter = (request.args.get("status") or "all").strip().lower()
    report_title = (request.args.get("report_title") or "Applicants Report").strip()
    report_notes = (request.args.get("notes") or "").strip()
    requested_filename = (request.args.get("filename") or "report").strip()

    safe_filename = "".join(
        ch for ch in requested_filename if ch.isalnum() or ch in ("-", "_", " ")
    ).strip() or "report"
    if not safe_filename.lower().endswith(".csv"):
        safe_filename = f"{safe_filename}.csv"

    filtered_applications = []
    for app_data in APPLICATIONS.values():
        app_status = str(app_data.get("status", "")).strip().lower()
        if status_filter != "all" and app_status != status_filter:
            continue
        filtered_applications.append(app_data)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Report Title", report_title])
    writer.writerow(["Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow(["Generated By", user.get("name", "HR User")])
    writer.writerow(["Status Filter", status_filter.title() if status_filter != "all" else "All Applicants"])
    if report_notes:
        writer.writerow(["Notes", report_notes])
    writer.writerow([])
    writer.writerow(["ID", "Name", "Surname", "Email", "Job", "Score", "Status", "Applied"])
    for a in filtered_applications:
        job = JOBS.get(a.get("job_id", ""), {})
        writer.writerow([
            a.get("id", ""), a.get("name", ""), a.get("surname", ""),
            a.get("email", ""), job.get("title", ""),
            a.get("score", ""), a.get("status", ""), a.get("uploaded_at", ""),
        ])
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'},
    )


@app.route("/hr/audit-log")
def hr_audit_log():
    user, err = _require_hr()
    if err:
        return err
    return redirect(url_for("audit_dashboard"))


# ─── Public job / apply routes ─────────────────────────────────────────────
@app.route("/jobs/<job_id>")
def job_detail(job_id):
    job_data = JOBS.get(job_id)
    if not job_data:
        flash("Job not found.", "danger")
        return redirect(url_for("index"))
    job = _wrap_job(_enrich_job(job_data))
    applications = [_wrap_app(a) for a in APPLICATIONS.values() if a.get("job_id") == job_id]
    return render_template("job_detail.html", job=job, applications=applications)


@app.route("/jobs/<job_id>/apply", methods=["GET", "POST"])
def apply(job_id):
    job_data = JOBS.get(job_id)
    if not job_data:
        flash("Job not found.", "danger")
        return redirect(url_for("index"))
    source = (request.args.get("source") or "").strip().lower()
    show_hr_sidebar = source == "hr"
    education_options = ["High School", "Diploma", "Bachelor's Degree", "Master's Degree", "PhD"]
    job = _wrap_job(_enrich_job(job_data))
    if request.method == "POST":
        import uuid
        from werkzeug.utils import secure_filename
        app_id = str(uuid.uuid4())
        resume_path = ""
        certification_paths = []
        upload_dir = Path(__file__).parent / "uploads"
        upload_dir.mkdir(exist_ok=True)

        resume_file = request.files.get("resume")
        if not resume_file or not resume_file.filename:
            flash("Please upload exactly one CV file.", "danger")
            return redirect(request.url)

        filename = secure_filename(resume_file.filename)
        save_path = upload_dir / f"{app_id}_cv_{filename}"
        resume_file.save(str(save_path))
        resume_path = str(save_path)

        cert_files = [f for f in request.files.getlist("certifications") if f and f.filename]
        if len(cert_files) > 200:
            flash("You can upload a maximum of 200 supporting files.", "danger")
            return redirect(request.url)

        for index, cert_file in enumerate(cert_files, start=1):
            cert_filename = secure_filename(cert_file.filename)
            cert_path = upload_dir / f"{app_id}_cert_{index}_{cert_filename}"
            cert_file.save(str(cert_path))
            certification_paths.append(str(cert_path))

        APPLICATIONS[app_id] = {
            "id": app_id,
            "job_id": job_id,
            "name": request.form.get("name", "").strip(),
            "surname": request.form.get("surname", "").strip(),
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "highest_education": request.form.get("highest_education", "").strip(),
            "note": request.form.get("note", "").strip(),
            "resume_path": resume_path,
            "certification_paths": certification_paths,
            "status": "pending",
            "score": 0,
            "summary": "",
            "recommendation": "",
            "matched_skills": [],
            "missing_skills": [],
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            with open(DATA_DIR / "applications.json", "w") as f:
                json.dump(APPLICATIONS, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save application: {e}")
        return redirect(url_for("success_page", application_id=app_id))
    return render_template(
        "apply.html",
        job=job,
        education_options=education_options,
        show_hr_sidebar=show_hr_sidebar,
    )


@app.route("/success")
def success_page():
    application_id = request.args.get("application_id", "")
    app_data = APPLICATIONS.get(application_id) or {}
    application = _wrap_app(app_data)
    job = _wrap_job(JOBS.get(app_data.get("job_id", "")) or {})
    return render_template("success.html", application=application, job=job)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    from flask import send_from_directory
    from werkzeug.utils import secure_filename
    safe_name = secure_filename(filename)
    upload_dir = Path(__file__).parent / "uploads"
    return send_from_directory(str(upload_dir), safe_name)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("HR System - Flask Application")
    print("=" * 60)
    print("URL:  http://localhost:5000")
    print("HR:   hr@company.com / password123")
    print("Audit: audit@company.com / password123")
    print("=" * 60 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=True)

    users_file = DATA_DIR / "users.json"
    if users_file.exists():
        try:
            with open(users_file, 'r') as f:
                USERS.update(json.load(f))
        except Exception as e:
            print(f"Warning: Could not load users: {e}")
    
    # Ensure default users exist
    if not USERS:
        USERS["user-001"] = {
            "id": "user-001",
            "email": "hr@company.com",
            "name": "HR Manager",
            "password_hash": generate_password_hash("password123"),
            "role": "hr"
        }
        USERS["user-002"] = {
            "id": "user-002",
            "email": "audit@company.com",
            "name": "Audit Manager",
            "password_hash": generate_password_hash("password123"),
            "role": "audit"
        }
        # Save default users
        try:
            with open(users_file, 'w') as f:
                json.dump(USERS, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save default users: {e}")
    
    # Load jobs
    jobs_file = DATA_DIR / "jobs.json"
    if jobs_file.exists():
        try:
            with open(jobs_file, 'r') as f:
                JOBS.update(json.load(f))
        except Exception as e:
            print(f"Warning: Could not load jobs: {e}")
    
    # Load applications
    apps_file = DATA_DIR / "applications.json"
    if apps_file.exists():
        try:
            with open(apps_file, 'r') as f:
                APPLICATIONS.update(json.load(f))
        except Exception as e:
            print(f"Warning: Could not load applications: {e}")

    # Load activity logs
    logs_file = DATA_DIR / "activity_logs.json"
    if logs_file.exists():
        try:
            with open(logs_file, 'r') as f:
                for entry in json.load(f):
                    # Parse timestamp string back to datetime if needed
                    if isinstance(entry.get('timestamp'), str):
                        try:
                            entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                        except Exception:
                            entry['timestamp'] = datetime.now(timezone.utc)
                    ACTIVITY_LOGS.append(entry)
        except Exception as e:
            print(f"Warning: Could not load activity logs: {e}")

# Load data at startup
load_all_data()

def log_activity(user_id, action, details="", status="success"):
    """Append an activity log entry and persist it."""
    entry = {
        "user_id": user_id,
        "action": action,
        "details": details,
        "status": status,
        "timestamp": datetime.now(timezone.utc),
    }
    ACTIVITY_LOGS.append(entry)
    # Persist (keep last 1000)
    try:
        serializable = []
        for e in ACTIVITY_LOGS[-1000:]:
            ec = dict(e)
            if isinstance(ec.get('timestamp'), datetime):
                ec['timestamp'] = ec['timestamp'].isoformat()
            serializable.append(ec)
        with open(DATA_DIR / "activity_logs.json", 'w') as f:
            json.dump(serializable, f, indent=2)
    except Exception as ex:
        print(f"Warning: Could not save activity logs: {ex}")

def get_current_user():
    """Get currently logged-in user"""
    if "user_id" in session:
        return USERS.get(session["user_id"])
    return None

@app.context_processor
def inject_user():
    """Make current user available in templates"""
    return {'current_user': get_current_user()}

@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

@app.route("/health")
def health():
    """Health check"""
    return jsonify({
        "status": "ok",
        "users": len(USERS),
        "jobs": len(JOBS),
        "applications": len(APPLICATIONS),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.route("/")
def index():
    """Redirect to dashboard"""
    user = get_current_user()
    if user:
        if user.get("role") == "audit":
            return redirect(url_for("audit_dashboard"))
        else:
            return redirect(url_for("hr_dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    """Login page"""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        
        # Find user
        user = None
        for u in USERS.values():
            if u.get("email", "").lower() == email:
                user = u
                break
        
        # Verify credentials
        if user and check_password_hash(user.get("password_hash", ""), password):
            session.permanent = True
            session["user_id"] = user["id"]
            
            if user.get("role") == "audit":
                return redirect(url_for("audit_dashboard"))
            else:
                return redirect(url_for("hr_dashboard"))
        else:
            flash("Invalid email or password.", "danger")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    """Logout"""
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


@app.route("/audit")
def audit_dashboard():
    """Audit Dashboard"""
    user = get_current_user()
    if not user:
        flash("Please log in.", "warning")
        return redirect(url_for("login"))
    if user.get("role") != "audit":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))

    PER_PAGE = 25
    page = max(1, request.args.get("page", 1, type=int))
    action_filter = request.args.get("action", "").strip().lower()

    all_logs = sorted(
        ACTIVITY_LOGS,
        key=lambda x: x.get("timestamp") or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True
    )
    filtered = [l for l in all_logs if action_filter in l.get("action", "").lower()] if action_filter else all_logs

    total_logs = len(all_logs)
    successful_count = sum(1 for l in all_logs if l.get("status") == "success")
    failed_count = sum(1 for l in all_logs if l.get("status") != "success")
    unique_users = len(set(l.get("user_id") for l in all_logs if l.get("user_id")))
    login_logs = [l for l in all_logs if l.get("action") in ("login", "logout")][:20]

    total_pages = max(1, (len(filtered) + PER_PAGE - 1) // PER_PAGE)
    page = min(page, total_pages)
    logs = filtered[(page - 1) * PER_PAGE: page * PER_PAGE]

    return render_template(
        "audit_dashboard.html",
        logs=logs,
        login_logs=login_logs,
        total_logs=total_logs,
        successful_count=successful_count,
        failed_count=failed_count,
        unique_users=unique_users,
        page=page,
        total_pages=total_pages,
        action_filter=action_filter,
    )

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("HR System - Flask Application")
    print("=" * 60)
    print(f"Starting on http://localhost:5000")
    print()
    print("Default Credentials:")
    print("  HR User:    hr@company.com / password123")
    print("  Audit User: audit@company.com / password123")
    print("=" * 60 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=True)


@app.route("/audit")
def audit_dashboard():
    """Audit Dashboard"""
    user = get_current_user()
    if not user:
        flash("Please log in.", "warning")
        return redirect(url_for("login"))
    
    if user.get("role") != "audit":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))
    
    return render_template("audit_dashboard.html")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("HR System - Flask Application")
    print("=" * 60)
    print(f"Starting on http://localhost:5000")
    print()
    print("Default Credentials:")
    print("  HR User:    hr@company.com / password123")
    print("  Audit User: audit@company.com / password123")
    print("=" * 60 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=True)


if __name__ == "__main__":
    print(f"Starting Flask app on port 5000...")
    try:
        app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    except Exception as e:
        print(f"ERROR running app: {e}")
        import traceback
        traceback.print_exc()

        user_dict['password_hash'] = user.password_hash  # Keep the hash
        users_data[user_id] = user_dict
    with open(DATA_DIR / "users.json", "w") as f:
        json.dump(users_data, f, indent=2, default=str)
    
    # Save activity logs
    logs_data = [_serialize_dataclass(log) for log in ACTIVITY_LOGS]
    with open(DATA_DIR / "activity_logs.json", "w") as f:
        json.dump(logs_data, f, indent=2, default=str)


def load_persistent_data() -> None:
    """Load jobs, applications, and users from JSON files."""
    _ensure_data_dir()
    
    # Try to load jobs
    jobs_file = DATA_DIR / "jobs.json"
    if jobs_file.exists():
        try:
            with open(jobs_file, "r") as f:
                jobs_data = json.load(f)
                for job_id, job_dict in jobs_data.items():
                    job_dict['due_date'] = datetime.fromisoformat(job_dict['due_date']) if job_dict.get('due_date') else None
                    job_dict['created_at'] = datetime.fromisoformat(job_dict['created_at']) if job_dict.get('created_at') else None
                    JOBS[job_id] = JobPosting(**job_dict)
        except Exception as e:
            print(f"Error loading jobs: {e}")
    
    # Try to load applications
    apps_file = DATA_DIR / "applications.json"
    if apps_file.exists():
        try:
            with open(apps_file, "r") as f:
                apps_data = json.load(f)
                for app_id, app_dict in apps_data.items():
                    if app_dict.get('created_at'):
                        app_dict['created_at'] = datetime.fromisoformat(app_dict['created_at'])
                    APPLICATIONS[app_id] = ApplicationRecord(**app_dict)
        except Exception as e:
            print(f"Error loading applications: {e}")
    
    # Try to load users
    users_file = DATA_DIR / "users.json"
    if users_file.exists():
        try:
            with open(users_file, "r") as f:
                users_data = json.load(f)
                for user_id, user_dict in users_data.items():
                    HR_USERS[user_id] = HRUser(**user_dict)
        except Exception as e:
            print(f"Error loading users: {e}")
    
    # Try to load activity logs
    logs_file = DATA_DIR / "activity_logs.json"
    if logs_file.exists():
        try:
            with open(logs_file, "r") as f:
                logs_data = json.load(f)
                for log_dict in logs_data:
                    log_dict['timestamp'] = datetime.fromisoformat(log_dict['timestamp']) if log_dict.get('timestamp') else None
                    ACTIVITY_LOGS.append(ActivityLog(**log_dict))
        except Exception as e:
            print(f"Error loading activity logs: {e}")


def hash_password(password: str) -> str:
    """Hash password with a salted adaptive algorithm."""
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return check_password_hash(password_hash, password)


def is_allowed_file(filename: str, allowed_extensions: set[str]) -> bool:
    if not filename or "." not in filename:
        return False
    return filename.rsplit(".", 1)[-1].lower() in allowed_extensions


def validate_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email or ""))


def validate_phone(phone: str) -> bool:
    return bool(PHONE_REGEX.match(phone or ""))


def validate_person_name(value: str) -> bool:
    return bool(value) and len(value) <= 80 and value.replace(" ", "").replace("-", "").isalpha()


def is_rate_limited(scope: str, key: str) -> bool:
    max_attempts, window_seconds = RATE_LIMITS[scope]
    now = time()
    bucket_key = f"{scope}:{key}"
    attempts = RATE_LIMIT_STORE[bucket_key]

    # Keep only recent entries in the rolling window.
    RATE_LIMIT_STORE[bucket_key] = [ts for ts in attempts if now - ts <= window_seconds]
    if len(RATE_LIMIT_STORE[bucket_key]) >= max_attempts:
        return True

    RATE_LIMIT_STORE[bucket_key].append(now)
    return False


def find_user_by_email(email: str) -> HRUser | None:
    """Find user by email."""
    for user in HR_USERS.values():
        if user.email.lower() == email.lower():
            return user
    return None


def log_activity(user_id: str, applicant_id: str, action: str, details: str = "") -> None:
    """Log user activity for audit trail."""
    log = ActivityLog(
        id=str(uuid4()),
        user_id=user_id,
        applicant_id=applicant_id,
        action=action,
        details=details
    )
    ACTIVITY_LOGS.append(log)


def seed_jobs() -> None:
    if JOBS:
        return

    job = JobPosting(
        id="hr-001",
        title="HR Operations & People Analyst",
        department="Human Resources",
        location="Hybrid",
        description=(
            "We are hiring an HR Operations & People Analyst with strong communication, "
            "recruitment support, Excel, data analysis, and process improvement skills. "
            "Applicants should have 2+ years of experience and a bachelor or master degree."
        ),
        due_date=datetime(2026, 6, 15, 17, 0, tzinfo=timezone.utc),
        application_link="http://127.0.0.1:5000/jobs/hr-001/apply",
        requirements=["Communication skills", "Excel proficiency", "2+ years HR experience", "Bachelor's degree"],
        custom_screening_criteria="Focus on data analysis skills and process improvement experience",
    )
    JOBS[job.id] = job


def login_required(f):
    """Decorator to require login for route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Backward-compatible decorator that now requires HR role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        user = HR_USERS.get(session['user_id'])
        if not user or user.role != 'hr':
            flash('HR access required.', 'danger')
            return redirect(url_for('hr_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def audit_required(f):
    """Decorator to require audit role for route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        user = HR_USERS.get(session['user_id'])
        if not user or user.role != 'audit':
            flash('Audit access required.', 'danger')
            return redirect(url_for('hr_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user() -> HRUser | None:
    """Get currently logged in user."""
    if 'user_id' in session:
        return HR_USERS.get(session['user_id'])
    return None


EDUCATION_LEVEL_OPTIONS = [
    "High School",
    "Diploma",
    "Associate Degree",
    "Bachelor's Degree",
    "Master's Degree",
    "Doctorate",
]


def get_job(job_id: str) -> JobPosting | None:
    return JOBS.get(job_id)


def current_deadline_state(job: JobPosting) -> str:
    now = datetime.now(timezone.utc)
    return "closed" if now >= job.due_date else "open"


def build_job_screening_text(job: JobPosting) -> str:
    parts = [job.title, job.department, job.location, job.description]
    if job.requirements:
        parts.append("Required requirements: " + ", ".join(job.requirements))
    if job.custom_screening_criteria:
        parts.append("Custom screening criteria: " + job.custom_screening_criteria)
    return " ".join(parts)


def refresh_job_application_links(base_url: str) -> None:
    base_url = base_url.rstrip("/")
    for job in JOBS.values():
        job.application_link = f"{base_url}/jobs/{job.id}/apply"


def screen_job_applications(job_id: str) -> list[ApplicationRecord]:
    job = get_job(job_id)
    if not job:
        return []

    applicants = [app for app in APPLICATIONS.values() if app.job_id == job_id]
    if not applicants:
        return []

    job_deadline_closed = current_deadline_state(job) == "closed"
    screening_text = build_job_screening_text(job)
    scored = rank_candidates(screening_text, [ResumeUpload(label=app.name, path=app.resume_path) for app in applicants])

    score_map = {item.filename: item for item in scored}
    for applicant in applicants:
        scored_candidate = score_map.get(applicant.resume_path.name)
        if scored_candidate:
            applicant.score = scored_candidate.score
            applicant.matched_skills = scored_candidate.matched_skills
            applicant.missing_skills = scored_candidate.missing_skills
            applicant.summary = scored_candidate.summary
            applicant.recommendation = scored_candidate.recommendation
            applicant.recommendation_reason = scored_candidate.recommendation_reason
            applicant.status = scored_candidate.status
            if job_deadline_closed and applicant.score >= 60:
                applicant.status = "shortlisted"
            elif job_deadline_closed and applicant.score < 60:
                applicant.status = "rejected"
            applicant.screened = True

    applicants.sort(key=lambda record: record.score, reverse=True)
    return applicants


def create_app() -> Flask:
    try:
        app = Flask(__name__)
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
        app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
        app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
        app.config["SESSION_COOKIE_HTTPONLY"] = True
        app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in production with HTTPS
        app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

        # Database Configuration - PostgreSQL
        db_user = os.environ.get("DB_USER", "postgres")
        db_password = os.environ.get("DB_PASSWORD", "postgres")
        db_host = os.environ.get("DB_HOST", "localhost")
        db_port = os.environ.get("DB_PORT", "5432")
        db_name = os.environ.get("DB_NAME", "hr_system")
        
        app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        
        # SMTP Configuration
        app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
        app.config["MAIL_PORT"] = int(os.environ.get("MAIL_PORT", 587))
        app.config["MAIL_USE_TLS"] = os.environ.get("MAIL_USE_TLS", True)
        app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")
        app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD", "")
        app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@company.com")

        if os.environ.get("FLASK_ENV") == "production":
            app.config["SESSION_COOKIE_SECURE"] = True

        UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        
        try:
            load_persistent_data()  # Load from disk first
        except Exception as e:
            print(f"Warning: Could not load persistent data: {e}")
        
        try:
            seed_jobs()  # Create defaults if no data loaded
            seed_users()  # Create default users if none loaded
            if not HR_USERS:
                seed_users()  # Ensure users exist
            save_persistent_data()  # Save initial state to disk
        except Exception as e:
            print(f"Warning: Could not initialize data: {e}")

        @app.context_processor
        def inject_user():
            """Make current user available in all templates."""
            return {
                'current_user': get_current_user(),
                'settings': SETTINGS,
            }

        @app.after_request
        def add_security_headers(response):
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Cache-Control"] = "no-store"
            return response

        @app.get("/health")
        def health():
            return jsonify({
                "status": "ok",
                "jobs": len(JOBS),
                "applications": len(APPLICATIONS),
                "utc_time": datetime.now(timezone.utc).isoformat(),
            })

        # ... rest of routes ...
        return app
    
    except Exception as e:
        print(f"CRITICAL ERROR in create_app: {e}")
        import traceback
        traceback.print_exc()
        raise  # Re-raise so we know there was a problem

    @app.get("/login")
    def login():
        if get_current_user():
            return redirect(url_for("hr_dashboard"))
        return render_template("login.html")

    @app.post("/login")
    def login_post():
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        if is_rate_limited("login", client_ip):
            flash("Too many login attempts. Please try again in a minute.", "danger")
            return redirect(url_for("login"))

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Email and password are required.", "danger")
            return redirect(url_for("login"))

        user = find_user_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("login"))

        if user.role not in {"hr", "audit"}:
            flash("This account type is not allowed to sign in.", "danger")
            return redirect(url_for("login"))

        session.permanent = True
        session["user_id"] = user.id
        user.last_login = datetime.now(timezone.utc)
        log_activity(user.id, "-", "login", f"Login successful from IP {client_ip}")
        flash(f"Welcome back, {user.name}!", "success")
        
        # Route based on user role
        if user.role == "audit":
            return redirect(url_for("audit_dashboard"))
        else:
            return redirect(url_for("hr_dashboard"))

    @app.get("/logout")
    def logout():
        current_user = get_current_user()
        if current_user:
            log_activity(current_user.id, "-", "logout", "User logged out")
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    @app.get("/")
    def index():
        refresh_job_application_links(request.url_root.rstrip("/"))
        jobs = list(JOBS.values())
        if jobs:
            return redirect(url_for("apply", job_id=jobs[0].id))
        flash("No open jobs are available right now.", "error")
        return redirect(url_for("hr_dashboard"))

    @app.get("/jobs/<job_id>")
    def job_detail(job_id: str):
        job = get_job(job_id)
        if not job:
            flash("Job posting not found.", "error")
            return redirect(url_for("index"))
        refresh_job_application_links(request.url_root.rstrip("/"))
        applicants = screen_job_applications(job_id)
        return render_template(
            "job_detail.html",
            job=job,
            applicants=applicants,
            app_base_url=request.url_root.rstrip("/"),
            deadline_state=current_deadline_state(job),
            application_link=job.application_link,
        )

    @app.route("/jobs/<job_id>/apply", methods=["GET", "POST"])
    def apply(job_id: str):
        job = get_job(job_id)
        if not job:
            flash("Job posting not found.", "error")
            return redirect(url_for("index"))

        source = request.args.get("source", "").strip().lower()
        show_hr_sidebar = source == "hr"

        if request.method == "GET":
            return render_template(
                "apply.html",
                job=job,
                education_options=EDUCATION_LEVEL_OPTIONS,
                show_hr_sidebar=show_hr_sidebar,
                source=source,
            )

        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")
        if is_rate_limited("apply", f"{job_id}:{client_ip}"):
            flash("Too many submissions from your network. Please wait a minute and try again.", "error")
            if source:
                return redirect(url_for("apply", job_id=job_id, source=source))
            return redirect(url_for("apply", job_id=job_id))

        name = request.form.get("name", "").strip()
        surname = request.form.get("surname", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        highest_education = request.form.get("highest_education", "").strip()
        upload = request.files.get("resume")
        cert_files = request.files.getlist("certifications")
        note = request.form.get("note", "").strip()

        if not name or not surname or not email or not phone or not highest_education or not upload or not upload.filename:
            flash("Add your full name, email, phone number, education, and resume before submitting.", "error")
            if source:
                return redirect(url_for("apply", job_id=job_id, source=source))
            return redirect(url_for("apply", job_id=job_id))

        if not validate_person_name(name) or not validate_person_name(surname):
            flash("Use valid alphabetic values for first and last name.", "error")
            if source:
                return redirect(url_for("apply", job_id=job_id, source=source))
            return redirect(url_for("apply", job_id=job_id))

        if not validate_email(email):
            flash("Please enter a valid email address.", "error")
            if source:
                return redirect(url_for("apply", job_id=job_id, source=source))
            return redirect(url_for("apply", job_id=job_id))

        if not validate_phone(phone):
            flash("Please enter a valid phone number.", "error")
            if source:
                return redirect(url_for("apply", job_id=job_id, source=source))
            return redirect(url_for("apply", job_id=job_id))

        if highest_education not in EDUCATION_LEVEL_OPTIONS:
            flash("Please select a valid education level.", "error")
            if source:
                return redirect(url_for("apply", job_id=job_id, source=source))
            return redirect(url_for("apply", job_id=job_id))

        filename = secure_filename(upload.filename)
        if not filename:
            flash("Please upload a valid resume file.", "error")
            if source:
                return redirect(url_for("apply", job_id=job_id, source=source))
            return redirect(url_for("apply", job_id=job_id))

        if not is_allowed_file(filename, ALLOWED_EXTENSIONS):
            flash("Supported resume formats are PDF, DOCX, and TXT.", "error")
            if source:
                return redirect(url_for("apply", job_id=job_id, source=source))
            return redirect(url_for("apply", job_id=job_id))

        unique_name = f"{uuid4().hex}_{filename}"
        target_path = UPLOAD_FOLDER / unique_name
        upload.save(target_path)

        application = ApplicationRecord(
            id=uuid4().hex,
            job_id=job_id,
            name=name,
            surname=surname,
            email=email,
            phone=phone,
            highest_education=highest_education,
            uploaded_at=datetime.now(timezone.utc),
            resume_path=target_path,
            note=note,
        )
        # Save certifications (optional)
        saved_certs: list[Path] = []
        if len([c for c in cert_files if c and c.filename]) > MAX_CERTIFICATIONS:
            flash(f"You can upload up to {MAX_CERTIFICATIONS} certification files.", "error")
            return redirect(url_for("apply", job_id=job_id, source=source) if source else url_for("apply", job_id=job_id))

        for c in cert_files:
            if not c or not c.filename:
                continue
            cfn = secure_filename(c.filename)
            if not cfn:
                continue
            if not is_allowed_file(cfn, ALLOWED_CERT_EXTENSIONS):
                flash("Certification files must be PDF, DOCX, TXT, PNG, JPG, or JPEG.", "error")
                return redirect(url_for("apply", job_id=job_id, source=source) if source else url_for("apply", job_id=job_id))
            c_unique = f"{uuid4().hex}_{cfn}"
            c_path = UPLOAD_FOLDER / c_unique
            c.save(c_path)
            saved_certs.append(c_path)

        application.certification_paths = saved_certs
        APPLICATIONS[application.id] = application
        save_persistent_data()  # Persist to disk

        if get_current_user():
            log_activity(get_current_user().id, application.id, "application_created_internal", f"Application created for job {job_id}")

        flash("Application submitted. HR will review it after the due date or from the dashboard.", "success")
        return redirect(url_for("application_success", job_id=job_id, application_id=application.id))

    @app.get("/jobs/<job_id>/apply/<application_id>/success")
    def application_success(job_id: str, application_id: str):
        job = get_job(job_id)
        application = APPLICATIONS.get(application_id)
        if not job or not application:
            flash("Application not found.", "error")
            return redirect(url_for("index"))
        return render_template("success.html", job=job, application=application)

    @app.get("/hr")
    @login_required
    def hr_dashboard():
        refresh_job_application_links(request.url_root.rstrip("/"))
        jobs = list(JOBS.values())
        selected_job_id = request.args.get("job", "").strip()
        selected_status = request.args.get("status", "").strip()
        sort_by = request.args.get("sort", "score").strip()
        dashboards = []
        all_applicants = []
        
        for job in jobs:
            if selected_job_id and job.id != selected_job_id:
                continue
            applicants = screen_job_applications(job.id)

            # apply optional status filter (e.g., shortlisted, rejected, interview, pending)
            status_counts: dict[str, int] = {}
            for app in applicants:
                app.job_ref = job
                all_applicants.append(app)
                status_counts[app.status] = status_counts.get(app.status, 0) + 1
            if selected_status:
                applicants = [a for a in applicants if a.status == selected_status]
            dashboards.append(
                {
                    "job": job,
                    "deadline_state": current_deadline_state(job),
                    "applicants": applicants,
                    "selected": [item for item in applicants if item.status == "shortlisted"],
                    "all_count": len(applicants),
                    "selected_count": len([item for item in applicants if item.status == "shortlisted"]),
                    "status_counts": status_counts,
                }
            )

        # Apply sorting
        if sort_by == "name":
            all_applicants.sort(key=lambda a: f"{a.name} {a.surname}")
        elif sort_by == "email":
            all_applicants.sort(key=lambda a: a.email)
        elif sort_by == "score":
            all_applicants.sort(key=lambda a: a.score, reverse=True)
        elif sort_by == "date":
            all_applicants.sort(key=lambda a: a.uploaded_at, reverse=True)
        elif sort_by == "status":
            all_applicants.sort(key=lambda a: a.status)

        return render_template(
            "hr_dashboard.html",
            dashboards=dashboards,
            all_applicants=all_applicants,
            app_base_url=request.url_root.rstrip("/"),
            selected_job_id=selected_job_id,
            selected_status=selected_status,
            sort_by=sort_by,
        )

    @app.get("/hr/jobs")
    @login_required
    def hr_jobs():
        refresh_job_application_links(request.url_root.rstrip("/"))
        jobs = list(JOBS.values())
        return render_template(
            "hr_jobs.html",
            jobs=jobs,
            deadline_state=lambda job: current_deadline_state(job),
            app_base_url=request.url_root.rstrip("/"),
        )

    @app.post("/hr/jobs/post")
    @admin_required
    def hr_post_job():
        title = request.form.get("title", "").strip()
        department = request.form.get("department", "").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()
        due_date_str = request.form.get("due_date", "").strip()
        requirements = request.form.get("requirements", "").strip()
        screening_criteria = request.form.get("screening_criteria", "").strip()

        if not all([title, department, location, description, due_date_str]):
            flash("All fields are required.", "error")
            return redirect(url_for("hr_jobs"))

        try:
            # Parse datetime-local format (YYYY-MM-DDTHH:mm)
            due_date = datetime.fromisoformat(due_date_str.replace("T", " ")).replace(tzinfo=timezone.utc)
        except ValueError:
            flash("Invalid date format.", "error")
            return redirect(url_for("hr_jobs"))

        job_id = f"job-{uuid4().hex[:8]}"
        application_link = f"{request.url_root.rstrip('/')}/jobs/{job_id}/apply"
        
        # Parse requirements (comma-separated)
        req_list = [r.strip() for r in requirements.split(',') if r.strip()] if requirements else []
        
        job = JobPosting(
            id=job_id,
            title=title,
            department=department,
            location=location,
            description=description,
            due_date=due_date,
            application_link=application_link,
            requirements=req_list,
            custom_screening_criteria=screening_criteria,
        )
        JOBS[job.id] = job
        user = get_current_user()
        if user:
            log_activity(user.id, "-", "job_posted", f"Posted job {job.title} ({job.id})")
        save_persistent_data()  # Persist to disk
        flash(f"Job '{title}' posted successfully. Application link: {application_link}", "success")
        return redirect(url_for("hr_jobs"))

    @app.get("/hr/jobs/<job_id>/export-shortlisted.csv")
    @login_required
    def export_shortlisted(job_id: str):
        job = get_job(job_id)
        if not job:
            flash("Job posting not found.", "error")
            return redirect(url_for("hr_dashboard"))

        applicants = screen_job_applications(job.id)
        shortlisted = [app for app in applicants if app.status == "shortlisted"]

        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["name", "surname", "email", "phone", "highest_education", "score", "status", "resume_file"])
        for applicant in shortlisted:
            writer.writerow([
                applicant.name,
                applicant.surname,
                applicant.email,
                applicant.phone,
                applicant.highest_education,
                applicant.score,
                applicant.status,
                applicant.resume_path.name,
            ])

        return Response(
            buffer.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{job.id}-shortlisted.csv"'},
        )

    @app.post("/hr/bulk-action")
    @login_required
    def hr_bulk_action():
        action = request.form.get("action", "").strip()
        app_ids = request.form.getlist("app_ids")
        if not action or not app_ids:
            flash("No action or applicants selected.", "error")
            return redirect(url_for("hr_dashboard"))

        count = 0
        for app_id in app_ids:
            app = APPLICATIONS.get(app_id)
            if app:
                if action == "shortlist":
                    app.status = "shortlisted"
                elif action == "reject":
                    app.status = "rejected"
                elif action == "interview":
                    app.status = "interview"
                elif action == "keep_warm":
                    app.status = "keep_warm"
                user = get_current_user()
                if user:
                    log_activity(user.id, app.id, "bulk_action", f"Applied {action}")
                count += 1
        flash(f"{count} applicant(s) {action}ed.", "success")
        return redirect(url_for("hr_dashboard"))

    @app.get("/hr/applications/<application_id>")
    @login_required
    def hr_application_detail(application_id: str):
        application = APPLICATIONS.get(application_id)
        if not application:
            flash("Applicant record not found.", "error")
            return redirect(url_for("hr_dashboard"))

        job = get_job(application.job_id)
        if not job:
            flash("Associated job not found.", "error")
            return redirect(url_for("hr_dashboard"))

        applicants = screen_job_applications(job.id)
        fresh_record = next((item for item in applicants if item.id == application.id), application)
        return render_template(
            "application_detail.html",
            job=job,
            application=fresh_record,
            app_base_url=request.url_root.rstrip("/"),
            deadline_state=current_deadline_state(job),
        )

    @app.post("/hr/applications/<application_id>/action")
    @login_required
    def hr_application_action(application_id: str):
        application = APPLICATIONS.get(application_id)
        if not application:
            flash("Applicant record not found.", "error")
            return redirect(url_for("hr_dashboard"))

        action = request.form.get("action")
        action_labels = {
            "shortlist": "shortlisted",
            "reject": "rejected",
            "interview": "moved to interview",
            "keep": "marked as keep warm",
        }
        if action == "shortlist":
            application.status = "shortlisted"
        elif action == "reject":
            application.status = "rejected"
        elif action == "interview":
            application.status = "interview"
        elif action == "keep":
            application.status = "keep_warm"
        else:
            flash("Unknown action.", "error")
            return redirect(url_for("hr_application_detail", application_id=application_id))

        user = get_current_user()
        if user:
            log_activity(user.id, application.id, "application_action", f"Changed status to {application.status}")

        flash(f"Application {action_labels.get(action, action)}.", "success")
        return redirect(url_for("hr_application_detail", application_id=application_id))

    @app.get("/hr/screening")
    @login_required
    def hr_screening():
        jobs = list(JOBS.values())
        all_applicants = []
        for job in jobs:
            applicants = screen_job_applications(job.id)
            for app in applicants:
                app.job_ref = job
                all_applicants.append(app)
        
        # Filter to show pending and screened applicants
        screened_applicants = [a for a in all_applicants if a.status in ['pending', 'shortlisted', 'rejected']]
        screened_applicants.sort(key=lambda a: a.uploaded_at, reverse=True)
        return render_template(
            "hr_screening.html",
            applicants=screened_applicants,
            pending=[a for a in screened_applicants if a.status == 'pending'],
            shortlisted=[a for a in screened_applicants if a.status == 'shortlisted'],
            rejected=[a for a in screened_applicants if a.status == 'rejected'],
            app_base_url=request.url_root.rstrip("/"),
        )

    @app.get("/hr/interviews")
    @login_required
    def hr_interviews():
        jobs = list(JOBS.values())
        all_applicants = []
        for job in jobs:
            applicants = screen_job_applications(job.id)
            for app in applicants:
                app.job_ref = job
                all_applicants.append(app)
        
        # Filter to show interview stage applicants
        interview_applicants = [a for a in all_applicants if a.status == 'interview']
        interview_applicants.sort(key=lambda a: a.uploaded_at, reverse=True)
        return render_template(
            "hr_interviews.html",
            applicants=interview_applicants,
            app_base_url=request.url_root.rstrip("/"),
        )

    @app.get("/hr/ratings")
    @login_required
    def hr_ratings():
        jobs = list(JOBS.values())
        all_applicants = []
        for job in jobs:
            applicants = screen_job_applications(job.id)
            for app in applicants:
                app.job_ref = job
                all_applicants.append(app)
        
        # Sort by score (highest first)
        all_applicants.sort(key=lambda a: a.score, reverse=True)
        return render_template(
            "hr_ratings.html",
            applicants=all_applicants,
            app_base_url=request.url_root.rstrip("/"),
        )

    @app.get("/hr/settings")
    @login_required
    def hr_settings():
        return render_template("hr_settings.html", settings=SETTINGS)

    @app.post("/hr/settings")
    @admin_required
    def hr_settings_update():
        company_name = request.form.get("company_name", "").strip()
        support_email = request.form.get("support_email", "").strip()
        default_view = request.form.get("default_view", "dashboard").strip()
        items_per_page = request.form.get("items_per_page", "25").strip()

        if company_name:
            SETTINGS.company_name = company_name[:120]

        if support_email:
            if not validate_email(support_email):
                flash("Support email is not valid.", "error")
                return redirect(url_for("hr_settings"))
            SETTINGS.support_email = support_email

        if default_view in {"dashboard", "applicants", "screening"}:
            SETTINGS.default_view = default_view

        try:
            ipp = int(items_per_page)
            if ipp in {10, 25, 50, 100}:
                SETTINGS.items_per_page = ipp
        except ValueError:
            flash("Items per page must be numeric.", "error")
            return redirect(url_for("hr_settings"))

        SETTINGS.notification_email_enabled = bool(request.form.get("notification_email_enabled"))
        SETTINGS.application_updates_enabled = bool(request.form.get("application_updates_enabled"))
        SETTINGS.interview_reminders_enabled = bool(request.form.get("interview_reminders_enabled"))
        SETTINGS.weekly_reports_enabled = bool(request.form.get("weekly_reports_enabled"))

        user = get_current_user()
        if user:
            log_activity(user.id, "-", "settings_updated", "Updated HR portal settings")

        flash("Settings updated successfully.", "success")
        return redirect(url_for("hr_settings"))

    @app.get("/hr/reports/summary.csv")
    @login_required
    def hr_report_summary():
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            "application_id",
            "job_id",
            "job_title",
            "full_name",
            "email",
            "phone",
            "score",
            "status",
            "uploaded_at_utc",
            "recommendation",
        ])

        for app_record in APPLICATIONS.values():
            job = get_job(app_record.job_id)
            writer.writerow([
                app_record.id,
                app_record.job_id,
                job.title if job else "Unknown",
                f"{app_record.name} {app_record.surname}",
                app_record.email,
                app_record.phone,
                app_record.score,
                app_record.status,
                app_record.uploaded_at.isoformat(),
                app_record.recommendation,
            ])

        return Response(
            buffer.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": 'attachment; filename="hr-summary-report.csv"'},
        )

    @app.get("/hr/audit")
    @admin_required
    def hr_audit_log():
        latest = sorted(ACTIVITY_LOGS, key=lambda item: item.timestamp, reverse=True)[:200]
        return jsonify([
            {
                "id": item.id,
                "user_id": item.user_id,
                "applicant_id": item.applicant_id,
                "action": item.action,
                "details": item.details,
                "timestamp": item.timestamp.isoformat(),
            }
            for item in latest
        ])

    @app.get("/audit")
    @audit_required
    def audit_dashboard():
        """Audit role dashboard - view activity logs."""
        # Get all activity logs sorted by newest first
        latest_logs = sorted(ACTIVITY_LOGS, key=lambda item: item.timestamp, reverse=True)
        
        # Get statistics
        total_logs = len(latest_logs)
        successful_logs = len([log for log in latest_logs if log.action != 'error'])
        failed_logs = len([log for log in latest_logs if log.action == 'error'])
        unique_users = len(set(log.user_id for log in latest_logs))
        
        # Get login-specific logs for timeline
        login_logs = [log for log in latest_logs if log.action == 'login'][:10]
        
        # Paginate logs (10 per page)
        page = request.args.get('page', 1, type=int)
        per_page = 10
        total_pages = (total_logs + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_logs = latest_logs[start_idx:end_idx]
        
        return render_template(
            'audit_dashboard.html',
            logs=paginated_logs,
            login_logs=login_logs,
            total_logs=total_logs,
            successful_count=successful_logs,
            failed_count=failed_logs,
            unique_users=unique_users,
            page=page,
            total_pages=total_pages,
            current_user=get_current_user()
        )

    @app.get("/uploads/<filename>")
    @login_required
    def uploaded_file(filename: str):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

    return app


# Global error holder for fallback app
_startup_error = None

try:
    print("Creating Flask app...")
    app = create_app()
    print("✓ Flask app created successfully")
except Exception as e:
    _startup_error = str(e)
    print(f"✗ FATAL ERROR during app initialization: {e}")
    import traceback
    traceback.print_exc()
    
    # Create a minimal fallback app that shows the error
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "fallback-key"
    
    error_msg = str(e)
    
    @app.get("/")
    def error_page():
        return f"""
        <h1 style="color: red;">⚠️ Application Error</h1>
        <p><strong>Error Message:</strong></p>
        <pre style="background: #f0f0f0; padding: 10px; border-radius: 5px;">
        {error_msg}
        </pre>
        <p><strong>Next Steps:</strong></p>
        <ul>
            <li>Run: <code>pip install -r requirements.txt</code></li>
            <li>Check the console output above for details</li>
            <li>Restart the application</li>
        </ul>
        """, 500
    
    @app.get("/login")
    def login_error():
        return error_page()[0], 503


if __name__ == "__main__":
    print(f"Starting Flask app on port 5000...")
    try:
        app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    except Exception as e:
        print(f"ERROR running app: {e}")
        import traceback
        traceback.print_exc()