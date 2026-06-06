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
    return redirect(url_for("login"))


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
            flash(f"Welcome, {user.get('name', 'User')}!", "success")
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

    return render_template(
        "hr_dashboard.html",
        dashboards=dashboards,
        applicants=list(APPLICATIONS.values())
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


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("HR System - Flask Application")
    print("=" * 60)
    print("URL:  http://localhost:5000")
    print("HR:   hr@company.com / password123")
    print("Audit: audit@company.com / password123")
    print("=" * 60 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=True)
