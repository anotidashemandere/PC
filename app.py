#!/usr/bin/env python
"""HR System Flask Application"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import os

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

    dashboards = []
    for job_id, job in JOBS.items():
        applicants = [a for a in APPLICATIONS.values() if a.get("job_id") == job_id]
        dashboards.append({
            "job": job,
            "applicants": applicants,
            "applicant_count": len(applicants),
        })

    all_applicants = list(APPLICATIONS.values())
    return render_template(
        "hr_dashboard.html",
        dashboards=dashboards,
        applicants=all_applicants,
        all_applicants=all_applicants,
    )


@app.route("/audit")
def audit_dashboard():
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

    # Sort newest first
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
        return val

    def __getitem__(self, key):
        return object.__getattribute__(self, '_d').get(key)

    def __bool__(self):
        return bool(object.__getattribute__(self, '_d'))


class _AppObj(_DictObj):
    @property
    def job_ref(self):
        job = JOBS.get(object.__getattribute__(self, '_d').get('job_id', ''))
        return _DictObj(job) if job else None


def _wrap_app(d):
    return _AppObj(d)


def _wrap_job(d):
    return _DictObj(d)


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
    jobs = [_wrap_job(j) for j in JOBS.values()]
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
        "requirements": request.form.get("requirements", "").strip(),
        "due_date": request.form.get("due_date", "").strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        with open(DATA_DIR / "jobs.json", "w") as f:
            json.dump(JOBS, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save job: {e}")
    flash("Job posted successfully.", "success")
    return redirect(url_for("hr_jobs"))


@app.route("/hr/screening")
def hr_screening():
    user, err = _require_hr()
    if err:
        return err
    all_apps = [_wrap_app(a) for a in APPLICATIONS.values()]
    pending = [a for a in all_apps if not a.status or a.status == "pending"]
    shortlisted = [a for a in all_apps if a.status == "shortlisted"]
    rejected = [a for a in all_apps if a.status == "rejected"]
    return render_template(
        "hr_screening.html",
        applicants=all_apps,
        pending=pending,
        shortlisted=shortlisted,
        rejected=rejected,
    )


@app.route("/hr/interviews")
def hr_interviews():
    user, err = _require_hr()
    if err:
        return err
    applicants = [_wrap_app(a) for a in APPLICATIONS.values()
                  if a.get("status") in ("shortlisted", "interview")]
    return render_template("hr_interviews.html", applicants=applicants)


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
    return render_template("hr_settings.html")


@app.route("/hr/settings/update", methods=["POST"])
def hr_settings_update():
    user, err = _require_hr()
    if err:
        return err
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
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Surname", "Email", "Job", "Score", "Status", "Applied"])
    for a in APPLICATIONS.values():
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
        headers={"Content-Disposition": "attachment; filename=report.csv"},
    )


@app.route("/hr/audit-log")
def hr_audit_log():
    user, err = _require_hr()
    if err:
        return err
    serializable = []
    for e in ACTIVITY_LOGS:
        ec = dict(e)
        if isinstance(ec.get("timestamp"), datetime):
            ec["timestamp"] = ec["timestamp"].isoformat()
        serializable.append(ec)
    return jsonify(serializable)


# ─── Public job / apply routes ─────────────────────────────────────────────
@app.route("/jobs/<job_id>")
def job_detail(job_id):
    job_data = JOBS.get(job_id)
    if not job_data:
        flash("Job not found.", "danger")
        return redirect(url_for("index"))
    job = _wrap_job(job_data)
    applications = [_wrap_app(a) for a in APPLICATIONS.values() if a.get("job_id") == job_id]
    return render_template("job_detail.html", job=job, applications=applications)


@app.route("/jobs/<job_id>/apply", methods=["GET", "POST"])
def apply(job_id):
    job_data = JOBS.get(job_id)
    if not job_data:
        flash("Job not found.", "danger")
        return redirect(url_for("index"))
    job = _wrap_job(job_data)
    if request.method == "POST":
        import uuid
        from werkzeug.utils import secure_filename
        app_id = str(uuid.uuid4())
        resume_path = ""
        resume_file = request.files.get("resume")
        if resume_file and resume_file.filename:
            filename = secure_filename(resume_file.filename)
            upload_dir = Path(__file__).parent / "uploads"
            upload_dir.mkdir(exist_ok=True)
            save_path = upload_dir / filename
            resume_file.save(str(save_path))
            resume_path = str(save_path)
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
            "certification_paths": [],
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
    return render_template("apply.html", job=job)


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

@app.route("/hr")
def hr_dashboard():
    """HR Dashboard"""
    user = get_current_user()
    if not user:
        flash("Please log in.", "warning")
        return redirect(url_for("login"))
    
    if user.get("role") != "hr":
        flash("Access denied.", "danger")
        return redirect(url_for("login"))
    
    dashboards = []
    for job_id, job in JOBS.items():
        applicants = [a for a in APPLICATIONS.values() if a.get("job_id") == job_id]
        dashboards.append({
            "job": job,
            "applicants": applicants,
            "applicant_count": len(applicants),
        })
    
    return render_template("hr_dashboard.html", dashboards=dashboards, applicants=list(APPLICATIONS.values()))

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