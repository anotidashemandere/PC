# HR System - Database & SMTP Setup Guide

## 1. PostgreSQL Database Setup

### Step 1: Connect to your existing PostgreSQL database (hr_system)

The application is configured to connect to your PostgreSQL `hr_system` database. Create a `.env` file in the project root with your database credentials:

```
# Copy from .env.example and update with your PostgreSQL details
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hr_system
```

### Step 2: Database Tables

The application will automatically create tables on first run. The tables created are:

- **jobs**: Job postings
- **applications**: Applicant records  
- **hr_users**: HR and Audit user accounts
- **activity_logs**: Audit trail

### Step 3: Verify Connection

Once configured, the app will:
1. Load existing data from PostgreSQL
2. Persist all job postings, applications, and user data
3. Automatically save changes to the database

## 2. Email (SMTP) Configuration

### Step 1: Choose Your Email Provider

#### Option A: Gmail (Recommended for Testing)

1. Go to https://myaccount.google.com/apppasswords
2. Create an "App Password" for Gmail
3. Add to `.env`:
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
```

#### Option B: Outlook/Office365

```
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@outlook.com
MAIL_PASSWORD=your-password
```

#### Option C: SendGrid

```
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=apikey
MAIL_PASSWORD=SG.your-sendgrid-api-key
```

#### Option D: Company Mail Server

```
MAIL_SERVER=your-company-mail.com
MAIL_PORT=587  # or 25, 465
MAIL_USE_TLS=True  # Set to False if using port 25
MAIL_USERNAME=your-email@company.com
MAIL_PASSWORD=your-password
```

### Step 2: Default Sender

Set the default email sender in `.env`:
```
MAIL_DEFAULT_SENDER=noreply@company.com
```

### Step 3: Enable Features

Once SMTP is configured, these features will work:
- Interview reminder emails
- Applicant status update notifications
- Bulk email campaigns to candidates

## 3. Installation Instructions

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Create .env File

```bash
# Copy the example file
copy .env.example .env

# Edit .env with your database and email credentials
```

### Step 3: Run the Application

```bash
python app.py
```

The app will start at `http://localhost:5000`

## 4. Login Credentials (Default)

After setup, log in with:

**HR Account:**
- Email: `hr@company.com`
- Password: `password123`

**Audit Account:**
- Email: `audit@company.com`  
- Password: `password123`

## 5. Troubleshooting

### Database Connection Issues

If you see "Failed to connect to database":
1. Verify PostgreSQL is running
2. Check DB credentials in `.env`
3. Ensure `hr_system` database exists
4. Verify user has proper permissions

```sql
-- Check if database exists
\l

-- Create database if needed
CREATE DATABASE hr_system;
```

### Email Not Sending

If interview reminders don't send:
1. Check SMTP credentials in `.env`
2. Verify MAIL_USERNAME and MAIL_PASSWORD are correct
3. For Gmail, ensure you used App Password (not regular password)
4. Check firewall allows outbound SMTP (port 587)
5. Enable "Less secure app access" if using personal Gmail

### Test Email Configuration

Create a test script:
```python
from flask_mail import Message
from flask import Flask
from flask_mail import Mail
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

mail = Mail(app)

with app.app_context():
    msg = Message('Test Email', recipients=['test@example.com'])
    msg.body = 'This is a test'
    mail.send(msg)
    print('Email sent successfully!')
```

## 6. Security Notes

- Never commit `.env` to version control
- Use strong passwords for database and email
- For production, use environment variables instead of `.env` file
- Update `SECRET_KEY` in `.env` for production
- Set `FLASK_ENV=production` and `SESSION_COOKIE_SECURE=True`

## 7. Next Steps

After setup:
1. Test database by posting a job - it should persist after app restart
2. Test email by scheduling an interview - reminder should send
3. Visit audit dashboard - should see activity logs
4. Try the new job view modal - should show candidates
5. Use "View All Applicants" to search all candidates across jobs

Need help? Check the application logs for detailed error messages.
