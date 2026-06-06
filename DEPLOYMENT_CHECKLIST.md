# Production Deployment Checklist

## 🔐 Security & Configuration

- [ ] Change `SECRET_KEY` to a strong random string
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```
- [ ] Set `FLASK_ENV=production`
- [ ] Set `DEBUG=False`
- [ ] Set `SESSION_COOKIE_SECURE=True`
- [ ] Enable HTTPS/SSL certificate
- [ ] Update all environment variables in `.env`:
  - `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD`
  - `DATABASE_URL` pointing to production PostgreSQL
  - `COMPANY_NAME`, `SUPPORT_EMAIL`
- [ ] Remove all default/test credentials
- [ ] Generate strong admin password
- [ ] Configure firewall rules
- [ ] Enable WAF (Web Application Firewall)

## 🗄️ Database

- [ ] PostgreSQL 12+ installed and running
- [ ] Database created: `hr_system`
- [ ] User created with strong password: `hr_admin`
- [ ] Run database migrations (see SETUP_GUIDE.md)
- [ ] Verify all tables created:
  ```sql
  SELECT table_name FROM information_schema.tables WHERE table_schema='public';
  ```
- [ ] Configure database backups (daily recommended)
- [ ] Test backup/restore procedure
- [ ] Enable PostgreSQL logging
- [ ] Configure connection pooling (PgBouncer recommended)
- [ ] Set up database monitoring

## 📧 Email Configuration

- [ ] Email service account configured
  - Gmail: App password generated
  - Office 365: MFA enabled
  - Corporate: SMTP credentials verified
- [ ] Test email sending:
  ```python
  from services.email_service import EmailService
  EmailService.send_application_received(
      'test@example.com', 'Test User', 'Test Job', 'app-001',
      'Company', 'support@company.com'
  )
  ```
- [ ] Verify email templates are professional
- [ ] Configure email from address (matches SMTP account)
- [ ] Set up email bounce handling
- [ ] Test all email types:
  - [ ] Application received
  - [ ] Shortlist notification
  - [ ] Interview invitation
  - [ ] Interview reminder
  - [ ] Rejection

## 🚀 Server & Deployment

- [ ] Web server configured (Gunicorn/uWSGI)
- [ ] Reverse proxy configured (Nginx/Apache)
- [ ] SSL/TLS certificates installed
- [ ] Application server starts automatically on reboot
- [ ] Process monitoring configured (supervisord/systemd)
- [ ] Log rotation configured
- [ ] CDN configured for static assets (optional)
- [ ] Gzip compression enabled
- [ ] Caching headers configured

## 📊 Application

- [ ] All dependencies installed from `requirements.txt`
- [ ] Python version compatible (3.8+)
- [ ] Virtual environment used
- [ ] Database tables verified with data
- [ ] Sample job posting created
- [ ] Admin user account created and tested
- [ ] First HR user account created
- [ ] Application accessible via HTTPS
- [ ] Redirect HTTP → HTTPS configured
- [ ] Static files served correctly
- [ ] Upload directory created and secured

## 🔄 Background Jobs

- [ ] APScheduler configured and running
- [ ] Background job scheduler logs verified
- [ ] Auto-screening job tested
- [ ] Interview reminder job tested
- [ ] Closing notification job tested
- [ ] Weekly report job tested
- [ ] Monitor background job execution
- [ ] Set up alerts for failed jobs

## 📱 UI/UX

- [ ] Responsive design tested on mobile/tablet
- [ ] All forms tested and validated
- [ ] File uploads working (PDF, DOCX, images)
- [ ] Charts and graphs rendering
- [ ] Pagination working correctly
- [ ] Search and filter functions working
- [ ] Navigation links all functional
- [ ] Error pages customized (404, 500, etc.)

## 📊 Monitoring & Logging

- [ ] Application logging configured
- [ ] Logs sent to appropriate location:
  - [ ] `hr_system.log` file
  - [ ] Syslog (optional)
  - [ ] Cloud logging service (optional)
- [ ] Error tracking configured (Sentry/Rollbar recommended)
- [ ] Performance monitoring enabled
- [ ] Uptime monitoring configured
- [ ] Alert notifications set up
- [ ] Dashboard created for monitoring metrics
- [ ] Log retention policy set (30+ days)

## 🔐 Access Control

- [ ] Admin dashboard protected
- [ ] Role-based access verified
- [ ] Audit log recording all actions
- [ ] IP whitelisting configured (optional)
- [ ] VPN/SSH access secured
- [ ] Password requirements enforced
- [ ] Session timeout configured (8 hours default)
- [ ] Rate limiting verified (login, apply)
- [ ] Two-factor authentication considered

## 📈 Performance

- [ ] Database queries optimized
- [ ] N+1 queries eliminated
- [ ] Indexes verified on key columns
- [ ] Connection pooling configured
- [ ] Static assets cached
- [ ] Minified CSS and JavaScript
- [ ] Image optimization completed
- [ ] Load testing completed
- [ ] Performance baseline established

## 🛡️ Backup & Disaster Recovery

- [ ] Daily database backups scheduled
- [ ] Backup testing procedure documented
- [ ] Backup storage redundant/off-site
- [ ] Disaster recovery plan documented
- [ ] RTO (Recovery Time Objective) defined
- [ ] RPO (Recovery Point Objective) defined
- [ ] Backup encryption enabled
- [ ] Retention policy configured (90+ days)

## 📋 Documentation

- [ ] Admin documentation created
- [ ] User manuals provided
- [ ] Emergency contacts listed
- [ ] Troubleshooting guide created
- [ ] Operations runbook prepared
- [ ] Deployment guide documented
- [ ] API documentation generated
- [ ] FAQ compiled

## 👥 User Management

- [ ] Admin account created and secured
- [ ] HR staff accounts created
- [ ] Interviewer accounts created (if applicable)
- [ ] Initial test data imported
- [ ] User onboarding process documented
- [ ] Password reset procedure tested
- [ ] Account deactivation tested

## 🧪 Testing

- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] End-to-end tests completed
- [ ] Browser compatibility tested
- [ ] Load testing completed
- [ ] Security scanning completed
- [ ] Penetration testing considered
- [ ] Data validation verified

## 🎯 Go-Live Preparation

- [ ] Team training completed
- [ ] Support procedures established
- [ ] Help desk contacted for training
- [ ] Communications plan executed
- [ ] Cutover plan finalized
- [ ] Rollback plan prepared
- [ ] Go-live date confirmed
- [ ] Stakeholders notified
- [ ] Parallel run period if applicable
- [ ] Post-launch support scheduled

## ✅ Launch Day

- [ ] Database backup taken
- [ ] Deployment executed
- [ ] Smoke tests passed
- [ ] Critical workflows verified
- [ ] Admin panels accessible
- [ ] User portals functional
- [ ] Emails sending correctly
- [ ] Monitoring active
- [ ] Support team on standby
- [ ] Document any issues

## 📊 Post-Launch (First Week)

- [ ] Monitor error rates
- [ ] Verify all jobs running
- [ ] Check database performance
- [ ] Review user feedback
- [ ] Monitor application logs
- [ ] Confirm backups completed
- [ ] Track any issues/bugs
- [ ] Verify email delivery
- [ ] Monitor CPU/Memory usage
- [ ] Establish baseline metrics

## 📈 Post-Launch (First Month)

- [ ] Analyze usage patterns
- [ ] Gather user feedback
- [ ] Identify performance bottlenecks
- [ ] Address critical bugs
- [ ] Document lessons learned
- [ ] Plan next phase improvements
- [ ] Review security logs
- [ ] Audit trail verification
- [ ] Capacity planning assessment
- [ ] Team retrospective

---

## Emergency Contacts

- **On-Call Support**: [Phone Number]
- **Database Admin**: [Name/Contact]
- **Network Admin**: [Name/Contact]
- **Email Support**: [Email]
- **Escalation Manager**: [Name/Contact]

---

## Key Metrics to Monitor

- Application response time (should be < 2 seconds)
- Database query time (should be < 500ms)
- Error rate (should be < 0.5%)
- Uptime (target: 99.9%)
- Failed login attempts
- Email delivery rate (should be > 99%)
- File upload success rate
- Background job completion time

---

## Quick Reference

### Database Commands

```bash
# Backup
pg_dump -U hr_admin hr_system > backup.sql

# Restore
psql -U hr_admin hr_system < backup.sql

# Connect
psql -U hr_admin -d hr_system
```

### Application Commands

```bash
# Start with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# View logs
tail -f hr_system.log

# Check processes
ps aux | grep gunicorn
```

### System Health Check

```sql
SELECT 
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM job_postings) as total_jobs,
    (SELECT COUNT(*) FROM applications) as total_applications,
    (SELECT COUNT(*) FROM activity_logs) as total_logs;
```

---

**Last Updated**: 2024  
**Status**: Ready for Production  
**Version**: 1.0.0 Enterprise
