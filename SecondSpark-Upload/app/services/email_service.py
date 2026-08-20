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


def send_otp_email(to: str, otp_code: str, name: str = 'Maker') -> bool:
    """
    Send OTP verification email via SMTP (Gmail / Custom SMTP provider).
    Returns True on success, False on failure.
    """
    try:
        # Load credentials directly from environment / config (support both SMTP_* and MAIL_*)
        mail_username = os.environ.get('SMTP_USER') or os.environ.get('MAIL_USERNAME', 'karnatihitesh@gmail.com')
        mail_password = os.environ.get('SMTP_PASS') or os.environ.get('MAIL_PASSWORD', '')
        mail_server   = os.environ.get('SMTP_HOST') or os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        mail_port     = int(os.environ.get('SMTP_PORT') or os.environ.get('MAIL_PORT', 587))
        sender_name   = 'SecondSpark'

        if not mail_password:
            logger.warning('[EmailService] SMTP password not configured in environment')
            return False

        # Construct multi-part message (plain text + rich HTML)
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'🔐 {otp_code} is your SecondSpark verification code'
        msg['From']    = f'{sender_name} <{mail_username}>'
        msg['To']      = to

        plain_text = (
            f"Hello {name},\n\n"
            f"Your SecondSpark verification code is: {otp_code}\n\n"
            f"This code will expire in 10 minutes. Do not share it with anyone.\n\n"
            f"If you did not request this code, you can safely ignore this email.\n\n"
            f"— SecondSpark Team"
        )
        html_text = build_otp_html(name=name, otp_code=otp_code, to_email=to)

        msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_text, 'html', 'utf-8'))

        # Direct TLS SMTP delivery
        with smtplib.SMTP(mail_server, mail_port, timeout=12) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(mail_username, mail_password)
            server.send_message(msg)

        logger.info(f'[EmailService] Successfully dispatched OTP email to {to}')
        return True

    except Exception as e:
        logger.error(f'[EmailService] Failed to send OTP email to {to}: {e}', exc_info=True)
        return False

