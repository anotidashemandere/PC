from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import csv
import os
import re
from collections import defaultdict
from pathlib import Path
from io import StringIO
from uuid import uuid4
from functools import wraps
from time import time

from flask import Flask, flash, redirect, render_template, request, url_for, send_from_directory, Response, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from services.cv_scoring import ResumeUpload, rank_candidates


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
ALLOWED_CERT_EXTENSIONS = {"pdf", "docx", "txt", "png", "jpg", "jpeg"}
MAX_CERTIFICATIONS = 5

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PHONE_REGEX = re.compile(r"^[0-9+()\-\s]{7,20}$")

RATE_LIMIT_STORE: dict[str, list[float]] = defaultdict(list)
RATE_LIMITS = {
    "login": (10, 60),  # max 10 attempts/minute/IP
    "apply": (20, 60),  # max 20 submissions/minute/IP
}


@dataclass
class JobPosting:
    id: str
    title: str
    department: str
    location: str
    description: str
    due_date: datetime
    application_link: str = ""
    requirements: list[str] = field(default_factory=list)
    custom_screening_criteria: str = ""


@dataclass
class ApplicationRecord:
    id: str
    job_id: str
    name: str
    surname: str
    email: str
    phone: str
    highest_education: str
    uploaded_at: datetime
    resume_path: Path
    certification_paths: list[Path] = field(default_factory=list)
    note: str = ""
    score: float = 0.0
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    summary: str = ""
    recommendation: str = "Pending"
    recommendation_reason: str = ""
    status: str = "pending"
    screened: bool = False
    interview_scheduled: bool = False
    interview_date: datetime | None = None
    interview_notes: str = ""
    hr_rating: float = 0.0
    hr_feedback: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class HRUser:
    id: str
    email: str
    name: str
    password_hash: str
    role: str = "hr"  # hr, admin
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: datetime | None = None


@dataclass
class ActivityLog:
    id: str
    user_id: str
    applicant_id: str
    action: str
    details: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AppSettings:
    company_name: str = "Global Modern Business"
    support_email: str = "support@company.com"
    notification_email_enabled: bool = True
    application_updates_enabled: bool = True
    interview_reminders_enabled: bool = True
    weekly_reports_enabled: bool = False
    default_view: str = "dashboard"
    items_per_page: int = 25


JOBS: dict[str, JobPosting] = {}
APPLICATIONS: dict[str, ApplicationRecord] = {}
HR_USERS: dict[str, HRUser] = {}
ACTIVITY_LOGS: list[ActivityLog] = []
SETTINGS = AppSettings()


def seed_users() -> None:
    """Initialize default HR users for demo."""
    if HR_USERS:
        return
    
    # Default admin user: admin@company.com / password123
    admin = HRUser(
        id="user-001",
        email="admin@company.com",
        name="Admin User",
        password_hash=hash_password("password123"),
        role="admin"
    )
    HR_USERS[admin.id] = admin
    
    # Default HR user: hr@company.com / password123
    hr_user = HRUser(
        id="user-002",
        email="hr@company.com",
        name="HR Manager",
        password_hash=hash_password("password123"),
        role="hr"
    )
    HR_USERS[hr_user.id] = hr_user
    
    # Default audit user: audit@company.com / password123
    audit_user = HRUser(
        id="user-003",
        email="audit@company.com",
        name="Audit Manager",
        password_hash=hash_password("password123"),
        role="audit"
    )
    HR_USERS[audit_user.id] = audit_user


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
    """Decorator to require admin role for route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        user = HR_USERS.get(session['user_id'])
        if not user or user.role != 'admin':
            flash('Admin access required.', 'danger')
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
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in production with HTTPS
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

    if os.environ.get("FLASK_ENV") == "production":
        app.config["SESSION_COOKIE_SECURE"] = True

    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    seed_jobs()
    seed_users()

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


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))