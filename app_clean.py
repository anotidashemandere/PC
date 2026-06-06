#!/usr/bin/env python
"""HR System Flask Application - Minimal Working Version"""
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

def load_all_data():
    """Load all data from disk"""
    global USERS, JOBS, APPLICATIONS
    
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

# Load data at startup
load_all_data()

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
            flash(f"Welcome, {user.get('name', 'User')}!", "success")
            
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
