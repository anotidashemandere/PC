"""
Background task scheduler for HR system.
Handles auto-screening, interview reminders, and job deadline notifications.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Manages background jobs and scheduled tasks."""
    
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler(daemon=True)
        self.app = app
        
    def init_app(self, app):
        """Initialize scheduler with Flask app."""
        self.app = app
        self.setup_jobs()
        
    def setup_jobs(self):
        """Configure scheduled background jobs."""
        
        # Run auto-screening check daily at 3 AM
        self.scheduler.add_job(
            self.check_and_screen_due_jobs,
            CronTrigger(hour=3, minute=0),
            id='auto_screen_due_jobs',
            name='Auto-screen due jobs',
            replace_existing=True
        )
        
        # Send interview reminders daily at 9 AM
        self.scheduler.add_job(
            self.send_interview_reminders,
            CronTrigger(hour=9, minute=0),
            id='send_reminders',
            name='Send interview reminders',
            replace_existing=True
        )
        
        # Send weekly reports every Monday at 8 AM
        self.scheduler.add_job(
            self.send_weekly_reports,
            CronTrigger(day_of_week='mon', hour=8, minute=0),
            id='weekly_reports',
            name='Send weekly reports',
            replace_existing=True
        )
        
        # Check for jobs closing soon daily at 10 AM
        self.scheduler.add_job(
            self.notify_closing_jobs,
            CronTrigger(hour=10, minute=0),
            id='closing_jobs_notification',
            name='Notify about closing jobs',
            replace_existing=True
        )
        
    def check_and_screen_due_jobs(self):
        """Auto-screen applications for jobs reaching due date."""
        try:
            from models import db, JobPosting, Application
            from services.cv_scoring import rank_candidates
            
            with self.app.app_context():
                # Find jobs with due date today or passed
                due_jobs = JobPosting.query.filter(
                    JobPosting.due_date <= datetime.now(),
                    JobPosting.status == 'open'
                ).all()
                
                for job in due_jobs:
                    try:
                        # Get unscreened applications
                        unscreened_apps = Application.query.filter(
                            Application.job_id == job.id,
                            Application.screened_at.is_(None)
                        ).all()
                        
                        if not unscreened_apps:
                            continue
                        
                        # Score all applications
                        resume_paths = [app.resume_path for app in unscreened_apps]
                        scores = rank_candidates(job.description, resume_paths)
                        
                        for app, score in zip(unscreened_apps, scores):
                            app.screening_score = score.get('score', 0)
                            app.matched_skills = score.get('matched_skills', [])
                            app.missing_skills = score.get('missing_skills', [])
                            app.screening_summary = score.get('summary', '')
                            app.recommendation = score.get('recommendation', '')
                            app.screened_at = datetime.now()
                            app.status = 'pending_review'
                        
                        db.session.commit()
                        logger.info(f"Auto-screened {len(unscreened_apps)} applications for job {job.id}")
                        
                    except Exception as e:
                        logger.error(f"Error screening job {job.id}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error in auto-screen job: {str(e)}")
    
    def send_interview_reminders(self):
        """Send reminders to candidates with interviews tomorrow."""
        try:
            from models import db, Interview
            from services.email_service import EmailService
            
            with self.app.app_context():
                tomorrow = datetime.now() + timedelta(days=1)
                tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0)
                tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59)
                
                # Find interviews scheduled for tomorrow
                upcoming_interviews = Interview.query.filter(
                    Interview.interview_date >= tomorrow_start,
                    Interview.interview_date <= tomorrow_end,
                    Interview.status == 'scheduled',
                    Interview.reminder_sent_at.is_(None)
                ).all()
                
                for interview in upcoming_interviews:
                    try:
                        app_record = interview.application
                        if not app_record:
                            continue
                        
                        job = app_record.job
                        EmailService.send_interview_reminder(
                            candidate_email=app_record.email,
                            candidate_name=app_record.full_name,
                            job_title=job.title,
                            interview_date=interview.interview_date,
                            interview_type=interview.interview_type,
                            company_name=self.app.config.get('COMPANY_NAME', 'Global Modern Business'),
                            support_email=self.app.config.get('SUPPORT_EMAIL', 'support@company.com')
                        )
                        
                        interview.reminder_sent_at = datetime.now()
                        db.session.commit()
                        logger.info(f"Sent reminder for interview {interview.id}")
                        
                    except Exception as e:
                        logger.error(f"Error sending interview reminder: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error in send reminders job: {str(e)}")
    
    def send_weekly_reports(self):
        """Generate and send weekly recruitment reports."""
        try:
            from models import db, JobPosting, Application
            from datetime import datetime, timedelta
            
            with self.app.app_context():
                week_ago = datetime.now() - timedelta(days=7)
                
                # Get stats for the past week
                new_applications = Application.query.filter(
                    Application.applied_at >= week_ago
                ).count()
                
                screened_applications = Application.query.filter(
                    Application.screened_at >= week_ago
                ).count()
                
                open_jobs = JobPosting.query.filter(
                    JobPosting.status == 'open'
                ).count()
                
                # Generate report (in production, would send email)
                report = {
                    'period': f"{week_ago.date()} to {datetime.now().date()}",
                    'new_applications': new_applications,
                    'screened_applications': screened_applications,
                    'open_positions': open_jobs
                }
                
                logger.info(f"Weekly report generated: {report}")
                
        except Exception as e:
            logger.error(f"Error in weekly reports job: {str(e)}")
    
    def notify_closing_jobs(self):
        """Notify about jobs closing within 3 days."""
        try:
            from models import db, JobPosting
            from datetime import datetime, timedelta
            
            with self.app.app_context():
                three_days = datetime.now() + timedelta(days=3)
                
                # Find jobs closing soon
                closing_jobs = JobPosting.query.filter(
                    JobPosting.due_date <= three_days,
                    JobPosting.due_date > datetime.now(),
                    JobPosting.status == 'open'
                ).all()
                
                for job in closing_jobs:
                    app_count = job.applications.count()
                    logger.info(
                        f"Job '{job.title}' closing soon ({job.due_date.date()}) "
                        f"with {app_count} applications"
                    )
                    
        except Exception as e:
            logger.error(f"Error in closing jobs notification: {str(e)}")
    
    def start(self):
        """Start the background scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Background task scheduler started")
    
    def stop(self):
        """Stop the background scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Background task scheduler stopped")


# Global scheduler instance
scheduler = TaskScheduler()
