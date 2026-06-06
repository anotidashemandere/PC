"""
Email service for HR system - handles all email notifications.
"""

from flask import render_template_string
from flask_mail import Mail, Message
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

mail = Mail()


class EmailService:
    """Service for sending professional emails."""

    TEMPLATES = {
        'interview_invitation': {
            'subject': 'Interview Invitation - {{company_name}}',
            'html': '''<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #124e66; color: white; padding: 20px; border-radius: 5px 5px 0 0; }
        .content { background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }
        .details { background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #124e66; }
        .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #666; }
        strong { color: #124e66; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Interview Invitation</h2>
        </div>
        <div class="content">
            <p>Dear {{candidate_name}},</p>
            
            <p>Congratulations! We are pleased to invite you to an interview for the <strong>{{job_title}}</strong> position at {{company_name}}.</p>
            
            <div class="details">
                <p><strong>Interview Details:</strong></p>
                <ul>
                    <li><strong>Position:</strong> {{job_title}}</li>
                    <li><strong>Date & Time:</strong> {{interview_date}}</li>
                    <li><strong>Interview Type:</strong> {{interview_type}}</li>
                    {% if interview_link %}
                    <li><strong>Meeting Link:</strong> <a href="{{interview_link}}">{{interview_link}}</a></li>
                    {% endif %}
                    {% if interview_location %}
                    <li><strong>Location:</strong> {{interview_location}}</li>
                    {% endif %}
                    {% if interviewer_name %}
                    <li><strong>Interviewer:</strong> {{interviewer_name}}</li>
                    {% endif %}
                </ul>
            </div>
            
            <p>Please confirm your attendance by replying to this email or contacting us at <strong>{{support_email}}</strong>.</p>
            
            <p>We look forward to speaking with you!</p>
            
            <p>Best regards,<br><strong>{{company_name}} Recruitment Team</strong></p>
            
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email directly.</p>
                <p>&copy; {{company_name}} - All rights reserved.</p>
            </div>
        </div>
    </div>
</body>
</html>'''
        },
        'shortlist_notification': {
            'subject': 'You Have Been Shortlisted - {{company_name}}',
            'html': '''<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #27ae60; color: white; padding: 20px; border-radius: 5px 5px 0 0; }
        .content { background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }
        .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #666; }
        strong { color: #27ae60; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🎉 Congratulations!</h2>
        </div>
        <div class="content">
            <p>Dear {{candidate_name}},</p>
            
            <p>We are excited to inform you that you have been <strong>shortlisted</strong> for the {{job_title}} position at {{company_name}}!</p>
            
            <p>Your qualifications and experience impressed our hiring team. Our recruitment specialist will contact you shortly with the next steps in the interview process.</p>
            
            <p>In the meantime, if you have any questions, please don't hesitate to reach out to us at <strong>{{support_email}}</strong>.</p>
            
            <p>Best regards,<br><strong>{{company_name}} Recruitment Team</strong></p>
            
            <div class="footer">
                <p>&copy; {{company_name}} - All rights reserved.</p>
            </div>
        </div>
    </div>
</body>
</html>'''
        },
        'rejection': {
            'subject': 'Application Status Update - {{company_name}}',
            'html': '''<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #7f8c8d; color: white; padding: 20px; border-radius: 5px 5px 0 0; }
        .content { background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }
        .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Application Status</h2>
        </div>
        <div class="content">
            <p>Dear {{candidate_name}},</p>
            
            <p>Thank you for your interest in the {{job_title}} position at {{company_name}}.</p>
            
            <p>After careful consideration of all applications, we have decided to move forward with other candidates whose experience more closely matches our current needs.</p>
            
            <p>We appreciate the time you invested in our application process and encourage you to apply for future positions that match your qualifications.</p>
            
            <p>Best regards,<br><strong>{{company_name}} Recruitment Team</strong></p>
            
            <div class="footer">
                <p>&copy; {{company_name}} - All rights reserved.</p>
            </div>
        </div>
    </div>
</body>
</html>'''
        },
        'interview_reminder': {
            'subject': 'Reminder: Your Interview is Tomorrow - {{company_name}}',
            'html': '''<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #f39c12; color: white; padding: 20px; border-radius: 5px 5px 0 0; }
        .content { background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }
        .details { background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #f39c12; }
        .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>⏰ Interview Reminder</h2>
        </div>
        <div class="content">
            <p>Dear {{candidate_name}},</p>
            
            <p>This is a friendly reminder about your upcoming interview with {{company_name}}.</p>
            
            <div class="details">
                <p><strong>Interview Details:</strong></p>
                <ul>
                    <li><strong>Date & Time:</strong> {{interview_date}}</li>
                    <li><strong>Position:</strong> {{job_title}}</li>
                    <li><strong>Type:</strong> {{interview_type}}</li>
                </ul>
            </div>
            
            <p>Please make sure to:</p>
            <ul>
                <li>Test your internet connection if it's a video interview</li>
                <li>Have your resume and any relevant documents ready</li>
                <li>Join 5-10 minutes early</li>
                <li>Find a quiet location for the interview</li>
            </ul>
            
            <p>If you need to reschedule or have questions, please contact us immediately at {{support_email}}.</p>
            
            <p>Best regards,<br><strong>{{company_name}} Recruitment Team</strong></p>
            
            <div class="footer">
                <p>&copy; {{company_name}} - All rights reserved.</p>
            </div>
        </div>
    </div>
</body>
</html>'''
        },
        'application_received': {
            'subject': 'We Received Your Application - {{company_name}}',
            'html': '''<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #124e66; color: white; padding: 20px; border-radius: 5px 5px 0 0; }
        .content { background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px; }
        .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Application Received</h2>
        </div>
        <div class="content">
            <p>Dear {{candidate_name}},</p>
            
            <p>Thank you for applying for the {{job_title}} position at {{company_name}}.</p>
            
            <p>We have received your application and will review your qualifications carefully. Our recruitment team will contact you within 3-5 business days with an update on your application status.</p>
            
            <p><strong>Application Details:</strong></p>
            <ul>
                <li>Position: {{job_title}}</li>
                <li>Application ID: {{application_id}}</li>
                <li>Submitted: {{submitted_date}}</li>
            </ul>
            
            <p>In the meantime, feel free to check our website for other career opportunities or contact us at {{support_email}} if you have any questions.</p>
            
            <p>Best regards,<br><strong>{{company_name}} Recruitment Team</strong></p>
            
            <div class="footer">
                <p>&copy; {{company_name}} - All rights reserved.</p>
            </div>
        </div>
    </div>
</body>
</html>'''
        }
    }

    @staticmethod
    def send_interview_invitation(candidate_email, candidate_name, job_title, interview_date, 
                                 interview_type, company_name, support_email, 
                                 interview_link=None, interview_location=None, interviewer_name=None):
        """Send interview invitation email to candidate."""
        try:
            template = EmailService.TEMPLATES['interview_invitation']
            html = render_template_string(
                template['html'],
                candidate_name=candidate_name,
                job_title=job_title,
                interview_date=interview_date.strftime('%B %d, %Y at %I:%M %p') if interview_date else 'TBD',
                interview_type=interview_type,
                interview_link=interview_link,
                interview_location=interview_location,
                interviewer_name=interviewer_name or 'Hiring Team',
                company_name=company_name,
                support_email=support_email
            )
            subject = render_template_string(template['subject'], company_name=company_name)
            
            msg = Message(
                subject=subject,
                recipients=[candidate_email],
                html=html,
                sender=support_email
            )
            mail.send(msg)
            logger.info(f"Interview invitation sent to {candidate_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send interview invitation: {str(e)}")
            return False

    @staticmethod
    def send_shortlist_notification(candidate_email, candidate_name, job_title, 
                                    company_name, support_email):
        """Send shortlist notification to candidate."""
        try:
            template = EmailService.TEMPLATES['shortlist_notification']
            html = render_template_string(
                template['html'],
                candidate_name=candidate_name,
                job_title=job_title,
                company_name=company_name,
                support_email=support_email
            )
            subject = render_template_string(template['subject'], company_name=company_name)
            
            msg = Message(
                subject=subject,
                recipients=[candidate_email],
                html=html,
                sender=support_email
            )
            mail.send(msg)
            logger.info(f"Shortlist notification sent to {candidate_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send shortlist notification: {str(e)}")
            return False

    @staticmethod
    def send_rejection(candidate_email, candidate_name, job_title, company_name, support_email):
        """Send rejection email to candidate."""
        try:
            template = EmailService.TEMPLATES['rejection']
            html = render_template_string(
                template['html'],
                candidate_name=candidate_name,
                job_title=job_title,
                company_name=company_name
            )
            subject = render_template_string(template['subject'], company_name=company_name)
            
            msg = Message(
                subject=subject,
                recipients=[candidate_email],
                html=html,
                sender=support_email
            )
            mail.send(msg)
            logger.info(f"Rejection email sent to {candidate_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send rejection email: {str(e)}")
            return False

    @staticmethod
    def send_interview_reminder(candidate_email, candidate_name, job_title, interview_date,
                               interview_type, company_name, support_email):
        """Send interview reminder email."""
        try:
            template = EmailService.TEMPLATES['interview_reminder']
            html = render_template_string(
                template['html'],
                candidate_name=candidate_name,
                job_title=job_title,
                interview_date=interview_date.strftime('%B %d, %Y at %I:%M %p') if interview_date else 'TBD',
                interview_type=interview_type,
                company_name=company_name,
                support_email=support_email
            )
            subject = render_template_string(template['subject'], company_name=company_name)
            
            msg = Message(
                subject=subject,
                recipients=[candidate_email],
                html=html,
                sender=support_email
            )
            mail.send(msg)
            logger.info(f"Interview reminder sent to {candidate_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send interview reminder: {str(e)}")
            return False

    @staticmethod
    def send_application_received(candidate_email, candidate_name, job_title, application_id,
                                  company_name, support_email):
        """Send application received confirmation."""
        try:
            template = EmailService.TEMPLATES['application_received']
            html = render_template_string(
                template['html'],
                candidate_name=candidate_name,
                job_title=job_title,
                application_id=application_id,
                submitted_date=datetime.now().strftime('%B %d, %Y'),
                company_name=company_name,
                support_email=support_email
            )
            subject = render_template_string(template['subject'], company_name=company_name)
            
            msg = Message(
                subject=subject,
                recipients=[candidate_email],
                html=html,
                sender=support_email
            )
            mail.send(msg)
            logger.info(f"Application received confirmation sent to {candidate_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send application received email: {str(e)}")
            return False
