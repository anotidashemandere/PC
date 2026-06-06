## ⚡ QUICK START - HR System Setup

### 🚨 IMPORTANT: Do This First!

1. **Open a terminal** in VS Code (Ctrl+` or Terminal menu)

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Restart Flask app**:
   - Kill the current "Run HR App" task (click the trash icon in Terminal panel)
   - Run the task again: Terminal → Run Task → "Run HR App"

4. **Wait 5 seconds**, then open: **http://localhost:5000/login**

---

### 📧 To Enable Email Features

**Option A: Gmail (Easy)**
1. Go to: https://myaccount.google.com/apppasswords
2. Select: Mail + Windows Computer  
3. Copy the 16-character password
4. Edit `.env` file in VS Code:
```
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=paste-16-char-password-here
```
5. Restart Flask app

**Option B: Use setup.py**
```bash
python setup.py
```
Follow the interactive prompts to configure email

---

### 🗄️ To Use PostgreSQL Database

1. Verify PostgreSQL is running on localhost:5432
2. Verify you have a database named `hr_system` created
3. Edit `.env` with your credentials:
```
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hr_system
```
4. Restart Flask app

---

### ✅ Test It Works

**Login Page:**
- URL: http://localhost:5000/login
- HR User: hr@company.com / password123
- Audit User: audit@company.com / password123

**Dashboard Features:**
- Click "View" on any job to see details and candidates
- Click "Edit" to modify job information  
- Click "Share" to copy application link
- Click "View All Applicants" to search across all jobs

**Health Check:**
- URL: http://localhost:5000/health
- Should show: `{"status": "ok", "jobs": X, "applications": Y, ...}`

---

### 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| App won't start | Install requirements: `pip install -r requirements.txt` |
| 404 Error | Make sure Flask app is running (check Terminal panel) |
| Can't login | Check `.env` file exists in `c:\Users\PC\hr\` |
| Email won't send | Verify MAIL_USERNAME and MAIL_PASSWORD in `.env` |
| Database error | Check PostgreSQL running on port 5432 |

---

### 📁 Files Created

- `.env` - Your configuration file (do NOT commit!)
- `.env.example` - Template for reference
- `setup.py` - Interactive configuration script
- `IMPLEMENTATION_COMPLETE.md` - Full documentation
- `DATABASE_SMTP_SETUP.md` - Detailed setup guide

---

**You're all set! The system is ready to use. Any questions? Check IMPLEMENTATION_COMPLETE.md for full documentation.**
