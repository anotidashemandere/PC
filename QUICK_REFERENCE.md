# 🚀 HR System - Quick Reference Card

## Installation (5 Minutes)

```bash
# 1. Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create PostgreSQL database
psql -U postgres
CREATE DATABASE hr_system;
CREATE USER hr_admin WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE hr_system TO hr_admin;

# 4. Create .env file with settings
FLASK_ENV=development
SECRET_KEY=your-secret
DATABASE_URL=postgresql://hr_admin:password@localhost:5432/hr_system

# 5. Run application
python app.py
```

---

## Key Files & What They Do

| File | Purpose | What's New |
|------|---------|-----------|
| `models.py` | Database models | ✅ SQLAlchemy ORM |
| `database_setup.py` | PostgreSQL schema | ✅ Full migration scripts |
| `config.py` | App configuration | ✅ Multi-environment support |
| `services/email_service.py` | Email notifications | ✅ 5 professional templates |
| `services/task_scheduler.py` | Background jobs | ✅ 4 automated tasks |
| `templates/careers.html` | Public job listing | ✅ Professional job board |
| `templates/audit_dashboard.html` | Activity tracking | ✅ Full audit trail viewer |
| `static/style.css` | Styling | ✅ Enterprise design |
| `requirements.txt` | Dependencies | ✅ PostgreSQL, Mail, APScheduler |
| `SETUP_GUIDE.md` | Setup instructions | ✅ 300+ page guide |

---

## Database Tables (7 Core)

```
users                  # HR staff accounts
job_postings          # Open positions
applications          # Candidate applications
interviews            # Interview scheduling
activity_logs         # Audit trail
system_settings       # Global config
email_templates       # Email designs
```

---

## Important Links

### Public URLs
- **Home**: http://localhost:5000/
- **Careers**: http://localhost:5000/careers
- **Apply**: http://localhost:5000/jobs/{job_id}/apply

### HR Portal
- **Dashboard**: http://localhost:5000/hr
- **Screening**: http://localhost:5000/hr/screening
- **Interviews**: http://localhost:5000/hr/interviews
- **Audit**: http://localhost:5000/hr/audit
- **Settings**: http://localhost:5000/hr/settings

---

## Email Configuration

### Gmail (Recommended)
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password (16 chars)
```

### Office 365
```env
MAIL_SERVER=smtp.office365.com
MAIL_PORT=587
MAIL_USERNAME=your-email@company.com
MAIL_PASSWORD=your-password
```

---

## Background Jobs Schedule

| Time | Task | What It Does |
|------|------|-------------|
| 3:00 AM | Auto-Screen | Scores applications for due jobs |
| 9:00 AM | Reminders | Sends interview reminder emails |
| 10:00 AM | Closing Alert | Notifies about jobs closing soon |
| Mon 8 AM | Weekly Report | Generates recruitment stats |

---

## Database Queries

### Get Applications
```sql
SELECT * FROM applications 
WHERE job_id = '...' 
ORDER BY screening_score DESC;
```

### Interview Schedule
```sql
SELECT * FROM interviews 
WHERE interview_date BETWEEN NOW() 
  AND NOW() + INTERVAL '7 days' 
ORDER BY interview_date;
```

### Login History
```sql
SELECT * FROM activity_logs 
WHERE action = 'login' 
ORDER BY created_at DESC 
LIMIT 50;
```

### Jobs Closing Soon
```sql
SELECT * FROM job_postings 
WHERE due_date BETWEEN NOW() 
  AND NOW() + INTERVAL '3 days' 
  AND status = 'open';
```

---

## Email Types (Auto-Sent)

1. **Application Received** → Candidate confirms application
2. **Shortlist Notification** → Candidate is shortlisted
3. **Interview Invitation** → Interview scheduled with details
4. **Interview Reminder** → 24 hours before interview
5. **Application Rejection** → Professional rejection message

---

## Security Checklist

```
✅ Password hashing (PBKDF2)
✅ Session security (HTTPOnly, Secure, SameSite)
✅ Rate limiting (10 login/min, 20 apply/min)
✅ Input validation (email, phone, files)
✅ Security headers (nosniff, sameorigin)
✅ CSRF protection
✅ SQL injection prevention (ORM)
✅ XSS protection (Jinja2 escaping)
```

---

## Troubleshooting

### Database Connection Failed
```bash
# Check if PostgreSQL is running
psql -U postgres -l

# Verify DATABASE_URL in .env
DATABASE_URL=postgresql://hr_admin:password@localhost:5432/hr_system
```

### Email Not Sending
```bash
# Test SMTP connection
python -c "from flask_mail import Mail; print('OK')"

# Verify credentials in .env
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Port Already in Use
```bash
# Kill existing process
lsof -ti :5000 | xargs kill -9

# Or use different port
python app.py --port 5001
```

---

## Useful Commands

```bash
# Start development server
python app.py

# Start production server (Gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Database backup
pg_dump -U hr_admin hr_system > backup.sql

# Database restore
psql -U hr_admin hr_system < backup.sql

# Connect to database
psql -U hr_admin -d hr_system

# Check application logs
tail -f hr_system.log
```

---

## Directory Structure

```
/hr/
├── app.py                    # Main application
├── models.py                 # Database models
├── config.py                 # Configuration
├── database_setup.py         # DB schema
├── services/
│   ├── cv_scoring.py        # CV ranking
│   ├── email_service.py     # Emails
│   └── task_scheduler.py    # Background jobs
├── templates/               # HTML pages
├── static/                  # CSS & assets
├── uploads/                 # Resume files
└── SETUP_GUIDE.md          # Full documentation
```

---

## Performance Tips

```
✅ Database indexes on common queries
✅ Pagination for large datasets
✅ Connection pooling (PgBouncer)
✅ Redis caching (optional)
✅ CDN for static files
✅ Gzip compression enabled
```

---

## First Time Setup

1. ✅ Follow SETUP_GUIDE.md
2. ✅ Create PostgreSQL database
3. ✅ Set environment variables
4. ✅ Run `python app.py`
5. ✅ Login at http://localhost:5000/login
6. ✅ Post first job
7. ✅ Test application form
8. ✅ Verify email sending

---

## Production Deployment

1. ✅ Use PostgreSQL (not SQLite)
2. ✅ Set SECRET_KEY
3. ✅ Set DEBUG=False
4. ✅ Enable HTTPS/SSL
5. ✅ Use Gunicorn/uWSGI
6. ✅ Setup reverse proxy (Nginx)
7. ✅ Configure email
8. ✅ Enable background jobs
9. ✅ Setup monitoring
10. ✅ Configure backups

See **DEPLOYMENT_CHECKLIST.md** for 100+ point checklist.

---

## Documentation

| Document | Content |
|----------|---------|
| **README.md** | Project overview, features, quick start |
| **SETUP_GUIDE.md** | Detailed installation & configuration |
| **DEPLOYMENT_CHECKLIST.md** | Production deployment guide |
| **IMPLEMENTATION_SUMMARY.md** | All features implemented |
| **This File** | Quick reference card |

---

## Support Resources

- **Flask Docs**: https://flask.palletsprojects.com/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Flask-Mail Docs**: https://pythonhosted.org/Flask-Mail/
- **APScheduler Docs**: https://apscheduler.readthedocs.io/

---

## Version Info

```
Application: HR System
Version: 1.0.0 Enterprise Edition
Status: ✅ Production Ready
Python: 3.8+
Database: PostgreSQL 12+
```

---

**Quick Wins** ⚡
- Email notifications working in 5 minutes
- Database setup in 10 minutes
- First job posting in 2 minutes
- Deploy to production in 30 minutes

---

**Last Updated**: 2024
**Keep this card handy for quick reference!**
