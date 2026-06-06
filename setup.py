#!/usr/bin/env python3
"""
HR System Setup Script
Helps configure PostgreSQL and SMTP settings
"""

import os
import sys
from pathlib import Path

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def create_env_file():
    print_section("STEP 1: Database Configuration")
    
    print("📦 PostgreSQL Database Settings")
    print("You have an existing 'hr_system' database in PostgreSQL.")
    print()
    
    db_user = input("Database User (default: postgres): ").strip() or "postgres"
    db_password = input("Database Password: ").strip() or "postgres"
    db_host = input("Database Host (default: localhost): ").strip() or "localhost"
    db_port = input("Database Port (default: 5432): ").strip() or "5432"
    db_name = input("Database Name (default: hr_system): ").strip() or "hr_system"
    
    print_section("STEP 2: Email (SMTP) Configuration")
    
    print("📧 Email Provider Setup")
    print("\nChoose your email provider:")
    print("1. Gmail (recommended for testing)")
    print("2. Outlook/Office365")
    print("3. SendGrid")
    print("4. Company Mail Server")
    
    choice = input("\nSelect (1-4): ").strip()
    
    mail_server = ""
    mail_port = ""
    mail_use_tls = "True"
    
    if choice == "1":
        print("\n📌 For Gmail:")
        print("1. Go to https://myaccount.google.com/apppasswords")
        print("2. Select 'Mail' and 'Windows Computer' (or your device)")
        print("3. Copy the 16-character password generated")
        mail_server = "smtp.gmail.com"
        mail_port = "587"
        mail_use_tls = "True"
    elif choice == "2":
        mail_server = "smtp-mail.outlook.com"
        mail_port = "587"
        mail_use_tls = "True"
    elif choice == "3":
        print("\n📌 For SendGrid:")
        print("1. Get your SendGrid API key from https://app.sendgrid.com/settings/api_keys")
        print("2. Use 'apikey' as username and your API key as password")
        mail_server = "smtp.sendgrid.net"
        mail_port = "587"
        mail_use_tls = "True"
    else:
        print("\n📌 For Company Mail Server:")
        mail_server = input("Mail Server Address: ").strip()
        mail_port = input("Mail Port (usually 587 or 25): ").strip()
        mail_use_tls = "True" if input("Use TLS? (y/n, default: y): ").strip().lower() != "n" else "False"
    
    mail_username = input("Email/Username: ").strip()
    mail_password = input("Password/API Key: ").strip()
    mail_sender = input("Default Sender Email (e.g., noreply@company.com): ").strip() or "noreply@company.com"
    
    # Create .env file
    env_content = f"""# Flask Configuration
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-this-in-production

# Database Configuration - PostgreSQL
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_HOST={db_host}
DB_PORT={db_port}
DB_NAME={db_name}

# SMTP Configuration - Email
MAIL_SERVER={mail_server}
MAIL_PORT={mail_port}
MAIL_USE_TLS={mail_use_tls}
MAIL_USERNAME={mail_username}
MAIL_PASSWORD={mail_password}
MAIL_DEFAULT_SENDER={mail_sender}
"""
    
    env_path = Path(__file__).parent / ".env"
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print_section("✅ Setup Complete!")
    print(f"✓ Configuration saved to: {env_path}")
    print("\n📋 Summary:")
    print(f"  Database: {db_name} @ {db_host}:{db_port}")
    print(f"  Mail Server: {mail_server}:{mail_port}")
    print(f"  Mail From: {mail_sender}")
    print("\n🚀 Next Steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Start the application: python app.py")
    print("3. Open browser: http://localhost:5000/login")
    print("4. Login with hr@company.com / password123")
    print("\n📚 For more details, see: DATABASE_SMTP_SETUP.md")

if __name__ == "__main__":
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
