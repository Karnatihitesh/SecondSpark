"""
SecondSpark Email Service
─────────────────────────
Sends transactional emails (OTP codes, notices) from karnatihitesh@gmail.com
via direct Gmail SMTP with HTML formatting and fallback plain text.
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app
from flask_mail import Mail

mail = Mail()
logger = logging.getLogger(__name__)

def build_otp_html(name: str, otp_code: str, to_email: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SecondSpark Verification Code</title>
</head>
<body style="margin:0;padding:0;background:#F8FAF9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F8FAF9;padding:40px 16px;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:20px;overflow:hidden;box-shadow:0 8px 30px rgba(0,0,0,0.08);max-width:560px;width:100%;">
        
        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#35C98A,#20a068);padding:36px 40px;text-align:center;">
            <div style="display:inline-flex;align-items:center;gap:10px;">
              <span style="background:rgba(255,255,255,0.25);border-radius:10px;padding:6px 12px;color:#fff;font-size:20px;font-weight:900;">⚡</span>
              <span style="color:#fff;font-size:24px;font-weight:800;letter-spacing:-0.03em;vertical-align:middle;">SecondSpark</span>
            </div>
            <p style="color:rgba(255,255,255,0.9);margin:8px 0 0;font-size:14px;">Give Unfinished Ideas a Second Spark</p>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:40px 40px 32px;">
            <h1 style="margin:0 0 8px;font-size:22px;color:#111827;font-weight:800;">Password Reset Verification</h1>
            <p style="margin:0 0 24px;color:#4B5563;font-size:15px;line-height:1.6;">
              Hello <strong>{name}</strong>,<br><br>
              A password reset was requested for your SecondSpark account (<strong>{to_email}</strong>).
              Use the 6-digit verification code below to proceed:
            </p>

            <!-- OTP Box -->
            <div style="background:#F0FDF4;border:2px solid #BBF7D0;border-radius:16px;padding:26px;text-align:center;margin-bottom:26px;">
              <div style="font-size:12px;color:#047857;text-transform:uppercase;letter-spacing:0.1em;font-weight:700;margin-bottom:6px;">Your 6-Digit Code</div>
              <div style="font-size:42px;font-weight:900;letter-spacing:0.2em;color:#111827;font-family:'Courier New',monospace;">{otp_code}</div>
              <div style="font-size:12px;color:#6B7280;margin-top:6px;">Expires in <strong>10 minutes</strong> · One-time use only</div>
            </div>

            <!-- Security Notice -->
            <div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:12px;padding:14px 18px;margin-bottom:24px;">
              <p style="margin:0;font-size:13px;color:#92400E;line-height:1.5;">
                🔒 <strong>Security Tip:</strong> Never share this code with anyone. SecondSpark support will never ask for your verification code.
              </p>
            </div>

            <p style="margin:0;color:#9CA3AF;font-size:13px;line-height:1.6;">
              If you didn't request this password reset, please ignore this email or change your password if you suspect unauthorized access.
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#F9FAFB;border-top:1px solid #E5E7EB;padding:20px 40px;text-align:center;">
            <p style="margin:0;font-size:12px;color:#9CA3AF;line-height:1.6;">
              © 2026 SecondSpark · Built with ⚡ by Karnati Hitesh &amp; Team<br>
              Direct contact: <a href="mailto:karnatihitesh@gmail.com" style="color:#35C98A;text-decoration:none;">karnatihitesh@gmail.com</a>
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def send_via_https_api(api_key: str, to: str, subject: str, html_text: str, from_email: str = None) -> bool:
    """Send transactional email via HTTPS REST API (Resend / SendGrid API over port 443)."""
    import urllib.request
    import json

    sender = from_email or os.environ.get('EMAIL_FROM') or 'SecondSpark <onboarding@resend.dev>'
    url = 'https://api.resend.com/emails'
    payload = {
        'from': sender,
        'to': [to],
        'subject': subject,
        'html': html_text
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'SecondSpark-Transporter'
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            if r.status in (200, 201):
                logger.info(f'[EmailService] Successfully delivered email to {to} via Resend HTTPS API')
                return True
    except Exception as e:
        logger.warning(f'[EmailService] HTTPS API delivery failed: {e}')
    return False


def send_otp_email(to: str, otp_code: str, name: str = 'Maker') -> bool:
    """
    Production Email Dispatcher:
    1. Checks for HTTPS Email API (RESEND_API_KEY / EMAIL_API_KEY) over port 443.
    2. Falls back to SMTP (Gmail / Custom SMTP) via SSL (465) / STARTTLS (587).
    Returns True on success, False on failure.
    """
    subject = f'🔐 {otp_code} is your SecondSpark verification code'
    plain_text = (
        f"Hello {name},\n\n"
        f"Your SecondSpark verification code is: {otp_code}\n\n"
        f"This code will expire in 10 minutes. Do not share it with anyone.\n\n"
        f"If you did not request this code, you can safely ignore this email.\n\n"
        f"— SecondSpark Team"
    )
    html_text = build_otp_html(name=name, otp_code=otp_code, to_email=to)

    # Provider 1: Resend / HTTPS API (Port 443 - Unblocked on all cloud platforms)
    resend_api_key = os.environ.get('RESEND_API_KEY') or os.environ.get('EMAIL_API_KEY')
    if resend_api_key:
        if send_via_https_api(api_key=resend_api_key, to=to, subject=subject, html_text=html_text):
            return True

    # Provider 2: SMTP Dispatch (Gmail / Custom SMTP)
    mail_username = os.environ.get('SMTP_USER') or os.environ.get('GMAIL_USER') or os.environ.get('MAIL_USERNAME', 'karnatihitesh@gmail.com')
    mail_password = os.environ.get('SMTP_PASS') or os.environ.get('GMAIL_APP_PASSWORD') or os.environ.get('MAIL_PASSWORD', '')
    mail_server   = os.environ.get('SMTP_HOST') or os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    mail_port     = int(os.environ.get('SMTP_PORT') or os.environ.get('MAIL_PORT', 587))
    sender_name   = 'SecondSpark'

    if not mail_password:
        logger.error('[EmailService] Neither RESEND_API_KEY nor SMTP_PASS/MAIL_PASSWORD is configured.')
        return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = f'{sender_name} <{mail_username}>'
    msg['To']      = to
    msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_text, 'html', 'utf-8'))

    # Try Port 465 SSL
    try:
        with smtplib.SMTP_SSL(mail_server, 465, timeout=8) as ssl_server:
            ssl_server.login(mail_username, mail_password)
            ssl_server.send_message(msg)
        logger.info(f'[EmailService] Successfully dispatched OTP email to {to} via SSL ({mail_server}:465)')
        return True
    except Exception as ssl_err:
        logger.warning(f'[EmailService] Port 465 SSL failed: {ssl_err}. Trying STARTTLS on port {mail_port}...')

    # Try Port 587 STARTTLS
    try:
        with smtplib.SMTP(mail_server, mail_port, timeout=8) as server:
            server.ehlo()
            if server.has_extn('starttls'):
                server.starttls()
                server.ehlo()
            server.login(mail_username, mail_password)
            server.send_message(msg)
        logger.info(f'[EmailService] Successfully dispatched OTP email to {to} via TLS ({mail_server}:{mail_port})')
        return True
    except Exception as tls_err:
        logger.error(f'[EmailService] All dispatch attempts failed for {to}: {tls_err}', exc_info=True)
        return False




