# HR System Setup & Deployment Guide

## 🎯 Project Overview

**Global Modern Business HR System** - A professional, enterprise-grade recruitment and applicant tracking system built with Flask, PostgreSQL, and modern web technologies.

### Key Features
- ✅ CV/Resume screening with AI-powered ranking
- ✅ Email notifications for interview invitations
- ✅ Automatic screening on job due dates
- ✅ Professional audit trail with login tracking
- ✅ Role-based access control (Admin/HR Staff/Interviewer)
- ✅ Background job scheduling
- ✅ Responsive professional UI
- ✅ Public job listing & application page

---

## 📋 Prerequisites

### Required Software
- **Python 3.8+**
- **PostgreSQL 12+**
- **pip** (Python package manager)
- **Git** (for version control)

### Optional
- **Redis** (for advanced caching and task queuing)
- **Docker** (for containerization)

---

## 🔧 Installation Steps

### Step 1: Clone/Setup Project

```bash
# Clone repository (or copy files to your directory)
cd /path/to/hr
```

### Step 2: Create Python Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Database Setup

#### Option A: Using PostgreSQL Locally

**Windows:**
```bash
# Download and install PostgreSQL from https://www.postgresql.org/download/windows/
# Add PostgreSQL to PATH
# Create database

psql -U postgres
CREATE DATABASE hr_system;
CREATE USER hr_admin WITH PASSWORD 'your_secure_password';
ALTER ROLE hr_admin SET client_encoding TO 'utf8';
ALTER ROLE hr_admin SET default_transaction_isolation TO 'read committed';
ALTER ROLE hr_admin SET default_transaction_deferrable TO on;
ALTER ROLE hr_admin SET default_transaction_read_only TO off;
GRANT ALL PRIVILEGES ON DATABASE hr_system TO hr_admin;
```

**macOS:**
```bash
# Using Homebrew
brew install postgresql
brew services start postgresql

# Create database
createdb hr_system
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql

# Connect and create database
sudo -u postgres psql
CREATE DATABASE hr_system;
CREATE USER hr_admin WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE hr_system TO hr_admin;
```

#### Option B: Using Docker PostgreSQL

```bash
docker run --name hr-postgres \
  -e POSTGRES_DB=hr_system \
  -e POSTGRES_USER=hr_admin \
  -e POSTGRES_PASSWORD=your_secure_password \
  -p 5432:5432 \
  -d postgres:15
```

### Step 5: Initialize Database Schema

```bash
# Run the migration script from database_setup.py
python -c "from database_setup import CREATE_TABLES, DATABASE_FUNCTIONS; print(CREATE_TABLES)"

# Or use psql directly
psql -U hr_admin -d hr_system < database_setup.sql

# Run triggers and functions
psql -U hr_admin -d hr_system -f database_setup.sql
```

### Step 6: Environment Configuration

Create a `.env` file in the project root:

```env
# Flask Settings
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=False

# Database
DATABASE_URL=postgresql://hr_admin:your_secure_password@localhost:5432/hr_system

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=noreply@company.com

# Company Settings
COMPANY_NAME=Global Modern Business
SUPPORT_EMAIL=support@company.com
SUPPORT_PHONE=+1-800-123-4567

# Feature Flags
ENABLE_AUTO_SCREENING=True
ENABLE_EMAIL_NOTIFICATIONS=True
ENABLE_BACKGROUND_JOBS=True
```

### Step 7: Update Flask App Initialization

Update your `app.py` to use the new database models and email service:

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from config import get_config
from models import db
from services.email_service import mail
from services.task_scheduler import scheduler

app = Flask(__name__)
app.config.from_object(get_config())

# Initialize extensions
db.init_app(app)
mail.init_app(app)
scheduler.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

# Start background scheduler
if app.config['ENABLE_BACKGROUND_JOBS']:
    scheduler.start()
```

---

## 📊 Database Schema

### Tables Created

1. **users** - HR system users with roles
2. **job_postings** - Job positions open for recruitment
3. **applications** - Job applications from candidates
4. **interviews** - Interview scheduling and tracking
5. **activity_logs** - Complete audit trail
6. **system_settings** - Global configuration
7. **email_templates** - Email notification templates

### Useful PostgreSQL Queries

#### 1. Get Applications by Job

```sql
SELECT a.id, a.full_name, a.email, a.screening_score, a.status
FROM applications a
JOIN job_postings j ON a.job_id = j.id
WHERE j.id = '{job_id}'
ORDER BY a.screening_score DESC;
```

#### 2. Interview Schedule

```sql
SELECT i.id, a.full_name, a.email, j.title, i.interview_date, 
       i.interview_type, u.full_name as interviewer
FROM interviews i
JOIN applications a ON i.application_id = a.id
JOIN job_postings j ON a.job_id = j.id
LEFT JOIN users u ON i.interviewer_id = u.id
WHERE i.interview_date BETWEEN CURRENT_TIMESTAMP 
      AND CURRENT_TIMESTAMP + INTERVAL '7 days'
ORDER BY i.interview_date;
```

#### 3. User Login Activity

```sql
SELECT created_at, action, ip_address, details
FROM activity_logs
WHERE user_id = '{user_id}' AND action IN ('login', 'logout')
ORDER BY created_at DESC
LIMIT 50;
```

#### 4. Jobs Closing Soon

```sql
SELECT id, title, due_date, 
       (SELECT COUNT(*) FROM applications WHERE job_id = j.id) as apps_count
FROM job_postings j
WHERE due_date BETWEEN CURRENT_TIMESTAMP 
      AND CURRENT_TIMESTAMP + INTERVAL '3 days'
AND status = 'open'
ORDER BY due_date;
```

#### 5. Audit Trail with Details

```sql
SELECT u.full_name, a.action, a.created_at, a.ip_address, 
       a.status, a.details
FROM activity_logs a
JOIN users u ON a.user_id = u.id
WHERE a.created_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY a.created_at DESC
LIMIT 100;
```

---

## 📧 Email Configuration

### Gmail Setup (Recommended for Testing)

1. Enable 2-Factor Authentication on your Gmail account
2. Generate App Password:
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Create & manage your Google Account
   - Security → App passwords
   - Select "Mail" and "Windows Computer"
   - Copy the generated 16-character password

3. Add to `.env`:
```env
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
```

### Corporate Email Setup

For Outlook/Office 365:
```env
MAIL_SERVER=smtp.office365.com
MAIL_PORT=587
MAIL_USERNAME=your-email@company.com
MAIL_PASSWORD=your-password
```

### Email Testing

```python
from services.email_service import EmailService
from datetime import datetime

EmailService.send_interview_invitation(
    candidate_email='candidate@example.com',
    candidate_name='John Doe',
    job_title='Software Engineer',
    interview_date=datetime.now(),
    interview_type='video',
    company_name='Global Modern Business',
    support_email='support@company.com',
    interview_link='https://zoom.us/j/123456'
)
```

---

## 🚀 Running the Application

### Development Server

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Run Flask development server
python app.py

# Access at http://localhost:5000
```

### Production Deployment

#### Using Gunicorn (Recommended)

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# With more options
gunicorn --workers=4 \
         --worker-class=sync \
         --bind=0.0.0.0:5000 \
         --timeout=120 \
         --access-logfile=- \
         --error-logfile=- \
         app:app
```

#### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Build and run:
```bash
docker build -t hr-system .
docker run -p 5000:5000 --env-file .env hr-system
```

---

## 🔒 Security Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Set `DEBUG = False` in production
- [ ] Use HTTPS/SSL certificates
- [ ] Set strong database passwords
- [ ] Configure secure email credentials
- [ ] Enable security headers (already done in code)
- [ ] Setup firewall rules
- [ ] Regular backups of PostgreSQL database
- [ ] Update dependencies regularly

---

## 🎯 Application Links

### Public Links (Share with Applicants)
- **Careers Page**: `http://your-domain.com/careers`
- **Apply for Job**: `http://your-domain.com/jobs/{job_id}/apply`
- **Application Confirmation**: `http://your-domain.com/jobs/{job_id}/apply/{app_id}/success`

### HR Portal (Admin Access)
- **HR Dashboard**: `http://your-domain.com/hr`
- **Job Screening**: `http://your-domain.com/hr/screening`
- **Interview Management**: `http://your-domain.com/hr/interviews`
- **Candidate Ratings**: `http://your-domain.com/hr/ratings`
- **Audit Trail**: `http://your-domain.com/hr/audit`
- **Settings**: `http://your-domain.com/hr/settings`

---

## 📱 Default Test Credentials

### Admin User (Create First)
```python
# Run this in Python shell with app context
from models import db, User
from werkzeug.security import generate_password_hash

admin = User(
    id='admin-001',
    email='admin@company.com',
    full_name='Admin User',
    role='admin',
    is_active=True
)
admin.set_password('SecurePassword123!')
db.session.add(admin)
db.session.commit()
```

---

## 🔄 Background Jobs Configuration

Jobs are automatically scheduled to run:

- **3:00 AM** - Auto-screen due job applications
- **9:00 AM** - Send interview reminders
- **10:00 AM** - Notify about closing positions
- **Monday 8:00 AM** - Generate and send weekly reports

To disable background jobs, set in `.env`:
```env
ENABLE_BACKGROUND_JOBS=False
```

---

## 📈 Performance Optimization

### Database Indexes

Already included in migration:
- `job_postings(status, due_date)`
- `applications(job_id, status, screening_score)`
- `activity_logs(user_id, created_at)`

### Caching Recommendations

```python
# Enable Redis caching (optional)
REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
```

### Query Optimization

Use pagination for large datasets:
```python
page = request.args.get('page', 1, type=int)
per_page = 25
applications = Application.query.paginate(page=page, per_page=per_page)
```

---

## 🐛 Troubleshooting

### Database Connection Error
```
Error: could not translate host name "localhost" to address
```
**Solution**: Ensure PostgreSQL is running and DATABASE_URL is correct

### Email Not Sending
```
Error: SMTPAuthenticationError
```
**Solution**: Verify MAIL_USERNAME and MAIL_PASSWORD in .env

### Port Already in Use
```
Error: Address already in use
```
**Solution**: 
```bash
# Kill existing process
lsof -ti :5000 | xargs kill -9

# Or use different port
python app.py --port 5001
```

### Permission Denied on Uploads
```
Error: Permission denied: 'uploads/'
```
**Solution**: 
```bash
mkdir -p uploads
chmod 755 uploads
```

---

## 📚 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Flask-Mail Documentation](https://pythonhosted.org/Flask-Mail/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)

---

## 📞 Support & Feedback

For issues or questions:
1. Check this guide's troubleshooting section
2. Review application logs in `hr_system.log`
3. Check PostgreSQL logs
4. Review Flask debug output in development mode

---

## 📝 License

This HR System is proprietary software for internal use.

---

**Last Updated**: 2024
**Version**: 1.0.0 (Enterprise Edition)
