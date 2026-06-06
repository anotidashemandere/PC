"""
PostgreSQL Database Migration and Setup Scripts.

Run these queries to set up the database schema.
"""

# ============================================================================
# MIGRATION: Create Database and Extensions
# ============================================================================

INIT_DATABASE = """
-- Create database
CREATE DATABASE hr_system
    ENCODING 'UTF8'
    LOCALE 'en_US.UTF-8'
    TEMPLATE template0;

-- Switch to new database
\\c hr_system

-- Create useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization
"""

# ============================================================================
# Core Tables - Auto-generated from SQLAlchemy models
# ============================================================================

CREATE_TABLES = """
-- Users table
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'hr' NOT NULL,
    department VARCHAR(255),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_login TIMESTAMP,
    last_login_ip VARCHAR(45)
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);

-- Job Postings table
CREATE TABLE job_postings (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    requirements JSONB,
    custom_screening_criteria TEXT,
    application_link VARCHAR(500),
    salary_range VARCHAR(100),
    employment_type VARCHAR(50) DEFAULT 'Full-time',
    due_date TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'open' NOT NULL,
    created_by VARCHAR(36) REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_job_postings_title ON job_postings(title);
CREATE INDEX idx_job_postings_status ON job_postings(status);
CREATE INDEX idx_job_postings_due_date ON job_postings(due_date);
CREATE INDEX idx_job_postings_status_due_date ON job_postings(status, due_date);

-- Applications table
CREATE TABLE applications (
    id VARCHAR(36) PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    highest_education VARCHAR(100) NOT NULL,
    resume_path VARCHAR(500) NOT NULL,
    certifications JSONB,
    cover_letter TEXT,
    screening_score FLOAT DEFAULT 0.0 NOT NULL CHECK (screening_score >= 0 AND screening_score <= 100),
    matched_skills JSONB,
    missing_skills JSONB,
    screening_summary TEXT,
    recommendation VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    hr_notes TEXT,
    hr_rating FLOAT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    screened_at TIMESTAMP,
    screened_by VARCHAR(36) REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_applications_job_id ON applications(job_id);
CREATE INDEX idx_applications_email ON applications(email);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_job_status ON applications(job_id, status);
CREATE INDEX idx_applications_score ON applications(screening_score DESC);

-- Interviews table
CREATE TABLE interviews (
    id VARCHAR(36) PRIMARY KEY,
    application_id VARCHAR(36) NOT NULL UNIQUE REFERENCES applications(id) ON DELETE CASCADE,
    interview_date TIMESTAMP NOT NULL,
    interview_type VARCHAR(50) DEFAULT 'phone' NOT NULL,
    interview_link VARCHAR(500),
    interview_location VARCHAR(500),
    interviewer_id VARCHAR(36) REFERENCES users(id),
    interview_notes TEXT,
    interviewer_rating FLOAT,
    interviewer_feedback TEXT,
    status VARCHAR(50) DEFAULT 'scheduled' NOT NULL,
    reminder_sent_at TIMESTAMP,
    email_sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_interviews_application_id ON interviews(application_id);
CREATE INDEX idx_interviews_interview_date ON interviews(interview_date);
CREATE INDEX idx_interviews_interviewer_id ON interviews(interviewer_id);
CREATE INDEX idx_interviews_status ON interviews(status);

-- Activity Logs table (Audit Trail)
CREATE TABLE activity_logs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    application_id VARCHAR(36) REFERENCES applications(id),
    action VARCHAR(100) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    details TEXT,
    changes_before JSONB,
    changes_after JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    status VARCHAR(50) DEFAULT 'success' NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_action ON activity_logs(action);
CREATE INDEX idx_activity_logs_created_at ON activity_logs(created_at DESC);
CREATE INDEX idx_activity_logs_user_date ON activity_logs(user_id, created_at DESC);
CREATE INDEX idx_activity_logs_action_date ON activity_logs(action, created_at DESC);

-- System Settings table
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) DEFAULT 'Global Modern Business' NOT NULL,
    company_logo_url VARCHAR(500),
    support_email VARCHAR(255) NOT NULL,
    support_phone VARCHAR(20),
    email_enabled BOOLEAN DEFAULT TRUE,
    smtp_host VARCHAR(255),
    smtp_port INTEGER,
    smtp_username VARCHAR(255),
    smtp_password VARCHAR(255),
    smtp_use_tls BOOLEAN DEFAULT TRUE,
    notify_on_application BOOLEAN DEFAULT TRUE,
    notify_on_interview BOOLEAN DEFAULT TRUE,
    notify_on_screening BOOLEAN DEFAULT TRUE,
    auto_screen_on_due_date BOOLEAN DEFAULT TRUE,
    auto_screen_enabled BOOLEAN DEFAULT TRUE,
    theme VARCHAR(50) DEFAULT 'light',
    items_per_page INTEGER DEFAULT 25,
    session_timeout_minutes INTEGER DEFAULT 480,
    password_reset_token_expiry_hours INTEGER DEFAULT 24,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Email Templates table
CREATE TABLE email_templates (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    subject VARCHAR(255) NOT NULL,
    body_html TEXT NOT NULL,
    body_text TEXT,
    variables JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_email_templates_name ON email_templates(name);
CREATE INDEX idx_email_templates_is_active ON email_templates(is_active);
"""

# ============================================================================
# USEFUL QUERIES FOR REPORTING AND ANALYTICS
# ============================================================================

ANALYTICS_QUERIES = """
-- 1. Get all applications for a specific job with scores
SELECT 
    a.id,
    a.full_name,
    a.email,
    a.phone,
    a.screening_score,
    a.status,
    a.applied_at,
    j.title as job_title
FROM applications a
JOIN job_postings j ON a.job_id = j.id
WHERE j.id = '{job_id}'
ORDER BY a.screening_score DESC;

-- 2. Get shortlisted candidates by job
SELECT 
    a.id,
    a.full_name,
    a.email,
    a.screening_score,
    COUNT(i.id) as interviews_scheduled
FROM applications a
LEFT JOIN interviews i ON a.id = i.application_id
WHERE a.job_id = '{job_id}' AND a.status = 'shortlisted'
GROUP BY a.id, a.full_name, a.email, a.screening_score
ORDER BY a.screening_score DESC;

-- 3. Interview schedule for next 7 days
SELECT 
    i.id,
    a.full_name,
    a.email,
    j.title as job_title,
    i.interview_date,
    i.interview_type,
    i.status,
    u.full_name as interviewer
FROM interviews i
JOIN applications a ON i.application_id = a.id
JOIN job_postings j ON a.job_id = j.id
LEFT JOIN users u ON i.interviewer_id = u.id
WHERE i.interview_date BETWEEN CURRENT_TIMESTAMP AND CURRENT_TIMESTAMP + INTERVAL '7 days'
AND i.status = 'scheduled'
ORDER BY i.interview_date ASC;

-- 4. Hiring funnel - count by status
SELECT 
    a.status,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM applications a
WHERE a.job_id = '{job_id}'
GROUP BY a.status
ORDER BY count DESC;

-- 5. Audit trail for specific user (login history)
SELECT 
    created_at,
    action,
    ip_address,
    status,
    details
FROM activity_logs
WHERE user_id = '{user_id}' AND action IN ('login', 'logout')
ORDER BY created_at DESC
LIMIT 50;

-- 6. Application statistics by date
SELECT 
    DATE(a.applied_at) as date,
    j.title as job_title,
    COUNT(*) as applications,
    ROUND(AVG(a.screening_score), 2) as avg_score,
    COUNT(CASE WHEN a.status = 'shortlisted' THEN 1 END) as shortlisted
FROM applications a
JOIN job_postings j ON a.job_id = j.id
GROUP BY DATE(a.applied_at), j.title
ORDER BY date DESC;

-- 7. Interviewer performance
SELECT 
    u.full_name,
    COUNT(i.id) as interviews_conducted,
    ROUND(AVG(i.interviewer_rating), 2) as avg_rating,
    COUNT(CASE WHEN i.status = 'completed' THEN 1 END) as completed
FROM interviews i
JOIN users u ON i.interviewer_id = u.id
WHERE i.status IN ('completed', 'scheduled')
GROUP BY u.id, u.full_name
ORDER BY interviews_conducted DESC;

-- 8. Users login activity
SELECT 
    u.id,
    u.email,
    u.full_name,
    COUNT(*) as login_count,
    MAX(u.last_login) as last_login,
    MAX(a.ip_address) as last_ip
FROM users u
LEFT JOIN activity_logs a ON u.id = a.user_id AND a.action = 'login'
GROUP BY u.id, u.email, u.full_name
ORDER BY MAX(u.last_login) DESC NULLS LAST;

-- 9. Jobs closing soon (within 3 days)
SELECT 
    id,
    title,
    department,
    due_date,
    (SELECT COUNT(*) FROM applications WHERE job_id = jp.id) as total_applications,
    (SELECT COUNT(*) FROM applications WHERE job_id = jp.id AND status = 'shortlisted') as shortlisted
FROM job_postings jp
WHERE due_date BETWEEN CURRENT_TIMESTAMP AND CURRENT_TIMESTAMP + INTERVAL '3 days'
AND status = 'open'
ORDER BY due_date ASC;

-- 10. Candidates with matching skills (for a specific job)
SELECT 
    a.id,
    a.full_name,
    a.email,
    a.matched_skills,
    a.screening_score,
    json_array_length(a.matched_skills) as matched_count
FROM applications a
WHERE a.job_id = '{job_id}'
ORDER BY json_array_length(a.matched_skills) DESC, a.screening_score DESC;
"""

# ============================================================================
# INITIAL DATA SETUP
# ============================================================================

INSERT_INITIAL_DATA = """
-- Insert default settings
INSERT INTO system_settings (company_name, support_email)
VALUES ('Global Modern Business', 'support@company.com')
ON CONFLICT DO NOTHING;

-- Insert email templates
INSERT INTO email_templates (id, name, subject, body_html, variables, is_active)
VALUES 
(
    'tpl_interview_invite',
    'interview_invitation',
    'Interview Invitation - {{company_name}}',
    '<html><body><h2>Dear {{candidate_name}},</h2><p>We are pleased to invite you to an interview for the {{job_title}} position.</p><p><strong>Interview Details:</strong></p><ul><li>Date & Time: {{interview_date}}</li><li>Type: {{interview_type}}</li><li>Link: {{interview_link}}</li><li>Interviewer: {{interviewer_name}}</li></ul><p>Please confirm your attendance by replying to this email.</p><p>Best regards,<br>{{company_name}} Recruitment Team</p></body></html>',
    '[\"candidate_name\", \"job_title\", \"interview_date\", \"interview_type\", \"interview_link\", \"interviewer_name\", \"company_name\"]'::jsonb,
    TRUE
),
(
    'tpl_rejection',
    'application_rejection',
    'Application Status - {{company_name}}',
    '<html><body><h2>Dear {{candidate_name}},</h2><p>Thank you for your interest in the {{job_title}} position at {{company_name}}.</p><p>After careful consideration, we have decided to move forward with other candidates.</p><p>We appreciate your time and encourage you to apply for future positions.</p><p>Best regards,<br>{{company_name}} Recruitment Team</p></body></html>',
    '[\"candidate_name\", \"job_title\", \"company_name\"]'::jsonb,
    TRUE
),
(
    'tpl_shortlist_notice',
    'shortlist_notification',
    'You Have Been Shortlisted - {{company_name}}',
    '<html><body><h2>Congratulations {{candidate_name}}!</h2><p>We are excited to inform you that you have been shortlisted for the {{job_title}} position.</p><p>Our hiring team will contact you soon with the next steps.</p><p>Best regards,<br>{{company_name}} Recruitment Team</p></body></html>',
    '[\"candidate_name\", \"job_title\", \"company_name\"]'::jsonb,
    TRUE
)
ON CONFLICT (name) DO NOTHING;
"""

# ============================================================================
# Database Helper Functions
# ============================================================================

DATABASE_FUNCTIONS = """
-- Function to update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for job_postings table
DROP TRIGGER IF EXISTS update_job_postings_updated_at ON job_postings;
CREATE TRIGGER update_job_postings_updated_at
    BEFORE UPDATE ON job_postings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for applications table
DROP TRIGGER IF EXISTS update_applications_updated_at ON applications;
CREATE TRIGGER update_applications_updated_at
    BEFORE UPDATE ON applications
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for interviews table
DROP TRIGGER IF EXISTS update_interviews_updated_at ON interviews;
CREATE TRIGGER update_interviews_updated_at
    BEFORE UPDATE ON interviews
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for system_settings table
DROP TRIGGER IF EXISTS update_system_settings_updated_at ON system_settings;
CREATE TRIGGER update_system_settings_updated_at
    BEFORE UPDATE ON system_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for email_templates table
DROP TRIGGER IF EXISTS update_email_templates_updated_at ON email_templates;
CREATE TRIGGER update_email_templates_updated_at
    BEFORE UPDATE ON email_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""

if __name__ == '__main__':
    print("PostgreSQL Migration Scripts")
    print("=" * 80)
    print("\nTo set up the database:")
    print("\n1. Run in psql:")
    print(INIT_DATABASE)
    print("\n2. Create tables:")
    print(CREATE_TABLES)
    print("\n3. Setup triggers and functions:")
    print(DATABASE_FUNCTIONS)
    print("\n4. Insert initial data:")
    print(INSERT_INITIAL_DATA)
