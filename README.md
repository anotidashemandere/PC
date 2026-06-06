# Global Modern Business HR System

**Professional Enterprise-Grade Recruitment & Applicant Tracking System**

Built with Flask, PostgreSQL, and modern web technologies for seamless recruitment operations.

---

## ⚡ Quick Start

### 1️⃣ Clone & Setup

```bash
cd /path/to/hr
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### 2️⃣ Database Setup

```bash
# PostgreSQL (Quick Setup)
psql -U postgres
CREATE DATABASE hr_system;
CREATE USER hr_admin WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE hr_system TO hr_admin;
\q

# Initialize schema
python -c "from database_setup import *; print('Setup complete')"
```

### 3️⃣ Configuration

Create `.env` file:

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://hr_admin:password@localhost:5432/hr_system
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
COMPANY_NAME=Global Modern Business
```

### 4️⃣ Run Application

```bash
python app.py
# Open http://localhost:5000
```

---

## 🎯 Features

### Recruitment Management
- ✅ **Job Postings** - Create and manage open positions
- ✅ **CV/Resume Screening** - AI-powered candidate ranking
- ✅ **Application Tracking** - Track all applicant information
- ✅ **Candidate Filtering** - Advanced search and filtering

### Communication
- ✅ **Email Notifications** - Automatic interview invitations
- ✅ **Interview Scheduling** - Schedule and manage interviews
- ✅ **Reminder System** - Automated interview reminders
- ✅ **Professional Templates** - Customizable email templates

### Operations
- ✅ **Auto-Screening** - Automatic ranking on job due date
- ✅ **Background Jobs** - Scheduled tasks and notifications
- ✅ **Bulk Actions** - Update multiple applications at once
- ✅ **Reports** - CSV export and analytics

### Security & Compliance
- ✅ **Audit Trail** - Complete activity logging with login tracking
- ✅ **Role-Based Access** - Admin, HR, and Interviewer roles
- ✅ **Password Security** - PBKDF2 hashing
- ✅ **Rate Limiting** - Protection against brute force attacks
- ✅ **Session Management** - Secure session handling

### User Experience
- ✅ **Professional UI** - Modern, responsive design
- ✅ **Public Careers Page** - Job listings for applicants
- ✅ **Mobile Responsive** - Works on all devices
- ✅ **Accessibility** - WCAG compliant

---

## 📊 System Architecture

```
├── app.py                      # Main Flask application
├── models.py                   # SQLAlchemy database models
├── config.py                   # Configuration management
├── database_setup.py           # PostgreSQL setup & queries
│
├── services/
│   ├── cv_scoring.py          # Resume/CV ranking engine
│   ├── email_service.py       # Email notifications
│   └── task_scheduler.py      # Background job scheduler
│
├── templates/                  # HTML templates
│   ├── index.html             # Public homepage
│   ├── careers.html           # Jobs listing page
│   ├── apply.html             # Application form
│   ├── hr_dashboard.html      # HR portal dashboard
│   ├── hr_screening.html      # Application screening
│   ├── hr_interviews.html     # Interview management
│   ├── audit_dashboard.html   # Audit trail viewer
│   └── ...
│
├── static/
│   ├── style.css              # Professional styling
│   └── ...
│
├── uploads/                    # Resume uploads
├── requirements.txt            # Python dependencies
├── SETUP_GUIDE.md             # Detailed setup guide
└── README.md                  # This file
```

---

## 🔗 Key Application Links

### For Applicants
- **Browse Jobs**: `http://your-domain.com/careers`
- **Apply**: `http://your-domain.com/jobs/<job_id>/apply`

### For HR Staff
- **Dashboard**: `http://your-domain.com/hr` (requires login)
- **Screening**: `http://your-domain.com/hr/screening`
- **Interviews**: `http://your-domain.com/hr/interviews`
- **Ratings**: `http://your-domain.com/hr/ratings`

### For Administrators
- **Settings**: `http://your-domain.com/hr/settings` (admin only)
- **Audit Trail**: `http://your-domain.com/hr/audit` (admin only)
- **Reports**: `http://your-domain.com/hr/reports/summary.csv` (admin only)

---

## 📧 Email Features

### Automatic Email Notifications

1. **Application Received** - Confirmation to applicant
2. **Shortlist Notification** - When candidate is shortlisted
3. **Interview Invitation** - With date, time, and meeting link
4. **Interview Reminder** - Day before interview
5. **Application Rejection** - Professional rejection letter

### Email Configuration

Using Gmail (recommended for testing):
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
```

---

## 🤖 Background Jobs

Automatically scheduled tasks:

| Time | Task | Description |
|------|------|-------------|
| 3:00 AM | Auto-Screen | Score applications for due jobs |
| 9:00 AM | Interview Reminders | Send reminders for upcoming interviews |
| 10:00 AM | Closing Notifications | Alert about jobs closing soon |
| Monday 8 AM | Weekly Report | Generate recruitment statistics |

---

## 🗄️ Database Schema

### Core Tables

- **users** - HR system users with roles
- **job_postings** - Open job positions
- **applications** - Candidate applications
- **interviews** - Interview scheduling
- **activity_logs** - Complete audit trail
- **system_settings** - Global configuration
- **email_templates** - Email notifications

### Sample Queries

```sql
-- Get applications for a job
SELECT * FROM applications WHERE job_id = '...' ORDER BY screening_score DESC;

-- Interview schedule (next 7 days)
SELECT * FROM interviews WHERE interview_date BETWEEN NOW() AND NOW() + INTERVAL '7 days';

-- User login history
SELECT * FROM activity_logs WHERE action = 'login' ORDER BY created_at DESC LIMIT 50;

-- Jobs closing soon
SELECT * FROM job_postings WHERE due_date BETWEEN NOW() AND NOW() + INTERVAL '3 days';
```

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for more detailed queries.

---

## 🔐 Security Features

| Feature | Implementation |
|---------|-----------------|
| Password Hashing | PBKDF2 via werkzeug |
| Session Security | Secure, HTTPOnly, SameSite cookies |
| Rate Limiting | Per-IP rate limits (10 login/min, 20 apply/min) |
| Input Validation | Email, phone, file extension checks |
| CSRF Protection | Flask session-based |
| SQL Injection | SQLAlchemy ORM protection |
| XSS Protection | Jinja2 auto-escaping |
| Security Headers | X-Content-Type-Options, X-Frame-Options, etc. |

---

## 📱 Responsive Design

- **Desktop**: Full-featured experience (1920px+)
- **Tablet**: Optimized layout (768px - 1024px)
- **Mobile**: Touch-friendly interface (<768px)

All components are fully responsive and accessible.

---

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production (Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker
```bash
docker build -t hr-system .
docker run -p 5000:5000 --env-file .env hr-system
```

### Cloud Deployment (Heroku, AWS, Azure, GCP)
See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions.

---

## 📋 Deployment Checklist

- [ ] Database is PostgreSQL (not SQLite)
- [ ] Email is configured and tested
- [ ] SECRET_KEY is changed
- [ ] DEBUG is set to False
- [ ] HTTPS/SSL is enabled
- [ ] Firewall rules are configured
- [ ] Database backups are scheduled
- [ ] Admin user account is created
- [ ] Audit logging is verified
- [ ] Background jobs are running

---

## 🐛 Troubleshooting

### Database Connection Failed
**Solution**: Verify PostgreSQL is running and DATABASE_URL is correct.

### Email Not Sending
**Solution**: Check MAIL_USERNAME and MAIL_PASSWORD in .env. Test with Gmail app password.

### Port 5000 Already in Use
**Solution**: Kill existing process or use different port: `python app.py --port 5001`

### Permission Errors on Upload
**Solution**: Ensure `uploads/` directory exists and is writable: `chmod 755 uploads`

For more issues, see [SETUP_GUIDE.md](SETUP_GUIDE.md) Troubleshooting section.

---

## 📚 Documentation

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Complete installation and configuration guide
- **[database_setup.py](database_setup.py)** - PostgreSQL schema and queries
- **[config.py](config.py)** - Application configuration reference
- **[models.py](models.py)** - Database models documentation

---

## 🎓 Default Test User

To create first admin user:

```python
# In Flask shell or Python environment
from app import app, db
from models import User

with app.app_context():
    admin = User(
        id='admin-001',
        email='admin@company.com',
        full_name='Admin User',
        role='admin'
    )
    admin.set_password('Admin@123')
    db.session.add(admin)
    db.session.commit()
    print("Admin user created!")
```

Login with:
- **Email**: admin@company.com
- **Password**: Admin@123

---

## 🤝 Support

For issues or questions:
1. Check documentation in [SETUP_GUIDE.md](SETUP_GUIDE.md)
2. Review application logs: `hr_system.log`
3. Check PostgreSQL logs
4. Enable DEBUG mode for detailed error messages

---

## 📝 License

**Proprietary Software**

This HR System is proprietary software for internal use. Unauthorized copying or distribution is prohibited.

---

## 📞 Contact

**Global Modern Business**
- Email: support@company.com
- Phone: +1-800-123-4567

---

## 🎉 Ready to Deploy?

1. ✅ Follow [SETUP_GUIDE.md](SETUP_GUIDE.md)
2. ✅ Configure `.env` file
3. ✅ Initialize PostgreSQL database
4. ✅ Test email notifications
5. ✅ Deploy to production
6. ✅ Monitor audit logs

**Version**: 1.0.0 (Enterprise Edition)  
**Last Updated**: 2024  
**Status**: ✅ Production Ready
