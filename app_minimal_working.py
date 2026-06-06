#!/usr/bin/env python
"""Minimal working Flask app - replace app.py with this if app won't start"""
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

def load_users():
    """Load users from disk"""
    users_file = DATA_DIR / "users.json"
    if users_file.exists():
        try:
            with open(users_file, 'r') as f:
                data = json.load(f)
                for user_id, user_data in data.items():
                    USERS[user_id] = user_data
        except:
            pass
    
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

load_users()

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "users": len(USERS),
        "utc_time": datetime.now(timezone.utc).isoformat(),
    })

@app.route("/")
def index():
    if "user_id" in session:
        user = USERS.get(session["user_id"])
        if user:
            if user["role"] == "audit":
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
            if u["email"].lower() == email.lower():
                user = u
                break
        
        if user and check_password_hash(user["password_hash"], password):
            session.permanent = True
            session["user_id"] = user["id"]
            flash(f"Welcome back, {user['name']}!", "success")
            
            if user["role"] == "audit":
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
        return redirect(url_for("login"))
    
    user = USERS.get(session["user_id"])
    if not user or user["role"] != "hr":
        flash("Access denied", "danger")
        return redirect(url_for("login"))
    
    return render_template("hr_dashboard.html", current_user=user)

@app.route("/audit")
def audit_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    user = USERS.get(session["user_id"])
    if not user or user["role"] != "audit":
        flash("Access denied", "danger")
        return redirect(url_for("login"))
    
    return render_template("audit_dashboard.html", current_user=user)

if __name__ == "__main__":
    print("Starting minimal Flask app on port 5000...")
    app.run(debug=True, host="0.0.0.0", port=5000)
