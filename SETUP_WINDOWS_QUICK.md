# ⚡ Quick Setup Guide - Windows

## 🎯 Complete Setup from Zero to Running (15 minutes)

---

## **Step 1: Open PowerShell (Administrator)**

Right-click on PowerShell and select "Run as Administrator"

```powershell
# Navigate to your project folder
cd C:\Users\PC\hr
```

---

## **Step 2: Create Virtual Environment**

```powershell
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# You should see (venv) prefix in your terminal
```

---

## **Step 3: Install All Dependencies**

```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

**This installs:**
- Flask (web framework)
- Flask-SQLAlchemy (database)
- Flask-Mail (email)
- APScheduler (background jobs)
- psycopg2 (PostgreSQL driver)
- And more...

---

## **Step 4: Setup PostgreSQL Database**

### **Option A: Using PostgreSQL on Windows (Recommended)**

**Install PostgreSQL if you don't have it:**
1. Download: https://www.postgresql.org/download/windows/
2. Install (remember the password you set for `postgres` user)
3. Open PowerShell and run:

```powershell
# Connect to PostgreSQL
psql -U postgres

# Then paste these commands one by one:
CREATE DATABASE hr_system;
CREATE USER hr_admin WITH PASSWORD 'password123';
ALTER ROLE hr_admin WITH SUPERUSER;
GRANT ALL PRIVILEGES ON DATABASE hr_system TO hr_admin;
\q
```

### **Option B: Using Docker (Alternative)**

```powershell
# Make sure Docker is installed and running

docker run -d `
  --name hr_postgres `
  -e POSTGRES_DB=hr_system `
  -e POSTGRES_USER=hr_admin `
  -e POSTGRES_PASSWORD=password123 `
  -p 5432:5432 `
  postgres:15
```

---

## **Step 5: Create .env File**

Create a file named `.env` in your project folder (`C:\Users\PC\hr\.env`)

**Copy this content:**

```env
# Database
DATABASE_URL=postgresql://hr_admin:password123@localhost:5432/hr_system

# Email (Gmail example - use your credentials)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Application Settings
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
COMPANY_NAME=My Company
```

### **Email Setup (Gmail):**
1. Go to: https://myaccount.google.com/apppasswords
2. Generate an "App Password" (16 characters)
3. Copy it to `MAIL_PASSWORD` in .env

**Note:** Regular Gmail password won't work. You MUST use App Password.

---

## **Step 6: Initialize Database Schema**

```powershell
# Run the database setup script
python database_setup.py
```

This creates:
- All 7 database tables
- Triggers for automatic timestamps
- Initial data (email templates, default users)

**Output should show:** ✅ Database initialized successfully

---

## **Step 7: Run the Application**

```powershell
# Start the Flask development server
python app.py
```

**You should see:**
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

---

## 🎉 Application is Running!

Open your browser and go to: **http://localhost:5000**

---

## 📝 Default Login Credentials

The system has two default users:

### **Admin Account**
```
Email: admin@company.com
Password: password123
```

### **HR Account**
```
Email: hr@company.com
Password: password123
```

---

## 🔐 How to Login

1. **Open browser**: http://localhost:5000
2. **Click "Login"** (top right corner)
3. **Enter credentials:**
   - Email: `admin@company.com`
   - Password: `password123`
4. **Click "Login"**

You're in! 🎉

---

## 🏢 After Login - What You Can Do

### **Dashboard** (http://localhost:5000/hr)
- See statistics
- View recent applications
- Quick access to all features

### **Jobs** (http://localhost:5000/hr/jobs)
- Create new job postings
- Edit existing jobs
- Set due dates
- Add custom screening criteria

### **Applications** (http://localhost:5000/hr/screening)
- View all applications
- See CV scores
- Read matched/missing skills
- Manage candidate status

### **Interviews** (http://localhost:5000/hr/interviews)
- Schedule interviews
- Assign interviewers
- Add meeting links
- Send reminders

### **Audit Trail** (http://localhost:5000/hr/audit)
- View all user activity
- See login history
- Track changes

### **Settings** (http://localhost:5000/hr/settings)
- Configure email
- Enable/disable features
- Change company info

---

## 🌍 Public Career Page

Your applicants can access:

**http://localhost:5000/careers**

Shows all open jobs with:
- Job descriptions
- Requirements
- "Apply Now" button

They can apply without logging in!

---

## 📧 Send Test Email

1. Go to **Settings** (http://localhost:5000/hr/settings)
2. Configure email settings
3. Go to **Jobs** and click "Edit" on any job
4. Change status to "Open"
5. Go to **Applications** and click email icon

---

## 🆘 Troubleshooting

### **"Cannot find Python" Error**
```powershell
# Use full path to Python
C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe -m venv venv
```

### **"Database connection failed"**
```powershell
# Check if PostgreSQL is running
psql -U postgres -c "SELECT 1"

# If error, start PostgreSQL service:
net start postgresql-x64-15
```

### **"ModuleNotFoundError"**
```powershell
# Make sure venv is activated (you see (venv) prefix)
# If not:
venv\Scripts\activate

# Then reinstall:
pip install -r requirements.txt
```

### **Port 5000 Already in Use**
```powershell
# Kill process using port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Or run on different port
python app.py --port 5001
```

### **Email Not Sending**
- Verify MAIL_USERNAME and MAIL_PASSWORD are correct
- For Gmail, use App Password (not regular password)
- Check Gmail Settings > Security > Less secure apps

---

## 💾 Backup Your Database

```powershell
# Backup
pg_dump -U hr_admin -d hr_system -f backup.sql

# Restore
psql -U hr_admin -d hr_system -f backup.sql
```

---

## 🔑 Change Default Password

1. Login as admin
2. Go to **Settings**
3. Look for user management
4. Change password

---

## 📊 Database is Running Correctly?

```powershell
# Test connection
python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://hr_admin:password123@localhost:5432/hr_system')
print('✅ Connected to database!')
"
```

---

## 🚀 Next Steps

1. ✅ Login with default credentials
2. ✅ Create your first job posting
3. ✅ Test the application form
4. ✅ Send test email
5. ✅ Invite real applicants to /careers page

---

## 📞 Need Help?

- **Setup Guide**: See `SETUP_GUIDE.md`
- **Quick Reference**: See `QUICK_REFERENCE.md`
- **Features**: See `README.md`
- **Deployment**: See `DEPLOYMENT_CHECKLIST.md`

---

## ✅ Checklist

- [ ] Python virtual environment created
- [ ] Dependencies installed
- [ ] PostgreSQL database created
- [ ] .env file created with correct settings
- [ ] Database schema initialized
- [ ] Application running on http://localhost:5000
- [ ] Logged in with admin@company.com / password123
- [ ] Can see HR dashboard

---

**You're all set! Start recruiting! 🚀**

Happy hiring! 🎉
