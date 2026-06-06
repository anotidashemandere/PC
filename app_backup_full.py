#!/usr/bin/env python
"""Minimal working Flask app for HR System"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

# Create data directory
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# In-memory storage (will load from disk)
USERS = {}
JOBS = {}
APPLICATIONS = {}

def load_users():
    """Load users from disk"""
    users_file = DATA_DIR / "users.json"
    if users_file.exists():
        try:
            with open(users_file, 'r') as f:
                data = json.load(f)
                USERS.update(data)
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

def load_jobs():
    """Load jobs from disk"""
    jobs_file = DATA_DIR / "jobs.json"
    if jobs_file.exists():
        try:
            with open(jobs_file, 'r') as f:
                data = json.load(f)
                JOBS.update(data)
        except Exception as e:
            print(f"Warning: Could not load jobs: {e}")

def load_applications():
    """Load applications from disk"""
    apps_file = DATA_DIR / "applications.json"
    if apps_file.exists():
        try:
            with open(apps_file, 'r') as f:
                data = json.load(f)
                APPLICATIONS.update(data)
        except Exception as e:
            print(f"Warning: Could not load applications: {e}")

# Load data on startup
load_users()
load_jobs()
load_applications()

def get_current_user():
    """Get the currently logged-in user"""
    if "user_id" in session:
        return USERS.get(session["user_id"])
    return None

@app.context_processor
def inject_user():
    """Make current user available in all templates"""
    return {'current_user': get_current_user()}

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "users": len(USERS),
        "jobs": len(JOBS),
        "applications": len(APPLICATIONS),
        "utc_time": datetime.now(timezone.utc).isoformat(),
    })

@app.route("/")
def index():
    if "user_id" in session:
        user = get_current_user()
        if user:
            if user.get("role") == "audit":
                return redirect(url_for("audit_dashboard"))
            else:
                return redirect(url_for("hr_dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        
        # Find user by email
        user = None
        for u in USERS.values():
            if u.get("email", "").lower() == email.lower():
                user = u
                break
        
        if user and check_password_hash(user.get("password_hash", ""), password):
            session.permanent = True
            session["user_id"] = user["id"]
            flash(f"Welcome back, {user.get('name', 'User')}!", "success")
            
            if user.get("role") == "audit":
                return redirect(url_for("audit_dashboard"))
            else:
                return redirect(url_for("hr_dashboard"))
        else:
            flash("Invalid email or password.", "danger")
    
    # Return the login template
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/hr")
def hr_dashboard():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))
    
    user = get_current_user()
    if not user or user.get("role") != "hr":
        flash("HR access required.", "danger")
        return redirect(url_for("login"))
    
    # Prepare dashboard data
    jobs_list = list(JOBS.values()) if JOBS else []
    applicants_list = list(APPLICATIONS.values()) if APPLICATIONS else []
    
    return render_template(
        "hr_dashboard.html",
        current_user=user,
        dashboards=[{"job": j, "applicants": [a for a in applicants_list if a.get("job_id") == j.get("id")]} for j in jobs_list] if jobs_list else []
    )

@app.route("/audit")
def audit_dashboard():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))
    
    user = get_current_user()
    if not user or user.get("role") != "audit":
        flash("Audit access required.", "danger")
        return redirect(url_for("login"))
    
    return render_template("audit_dashboard.html", current_user=user)

if __name__ == "__main__":
    print("=" * 60)
    print("Starting HR System Flask app on port 5000...")
    print("=" * 60)
    print(f"Login with:")
    print(f"  HR:    hr@company.com / password123")
    print(f"  Audit: audit@company.com / password123")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
