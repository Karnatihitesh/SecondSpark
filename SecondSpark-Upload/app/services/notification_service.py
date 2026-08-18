import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
from app.models.user import db, User
from app.models.notification import Notification


def send_email_async(to_email, subject, html_content):
    """
    Sends an email asynchronously via SMTP if configured, 
    otherwise logs a formatted preview to the server console.
    """
    smtp_server = os.environ.get('SMTP_SERVER')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))
    smtp_user = os.environ.get('SMTP_USER')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    from_email = os.environ.get('FROM_EMAIL', 'notifications@secondspark.dev')

    def _send():
        if smtp_server and smtp_user and smtp_password:
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = f"[SecondSpark] {subject}"
                msg['From'] = f"SecondSpark <{from_email}>"
                msg['To'] = to_email

                part = MIMEText(html_content, 'html')
                msg.attach(part)

                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.sendmail(from_email, to_email, msg.as_string())
                print(f"[Email Service] Email sent successfully to {to_email}: {subject}")
            except Exception as err:
                print(f"[Email Service] Failed to send email to {to_email}: {err}")
        else:
            # Simulated email dispatch with rich console preview
            print("\n" + "="*60)
            print(f"[SecondSpark Email Notification Dispatch]")
            print(f" To:      {to_email}")
            print(f" Subject: [SecondSpark] {subject}")
            print(f" Status:  Delivered (Dev/Simulation Mode)")
            print("="*60 + "\n")

    threading.Thread(target=_send, daemon=True).start()


def create_notification(user_id, notif_type, title, message, link=None, send_email=True):
    """
    Persists a notification in the database and triggers email alert if configured.
    """
    try:
        notif = Notification(
            user_id=user_id,
            type=notif_type,
            title=title,
            message=message,
            link=link,
            is_read=False
        )
        db.session.add(notif)
        db.session.commit()

        if send_email:
            user = db.session.get(User, user_id)
            if user and user.email:
                email_html = f"""
                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 580px; margin: 0 auto; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; padding: 24px;">
                    <div style="background: #EAFBF3; padding: 12px 18px; border-radius: 8px; margin-bottom: 20px; display: inline-block;">
                        <span style="color: #35C98A; font-weight: bold; font-size: 16px;">⚡ SecondSpark</span>
                    </div>
                    <h2 style="color: #111827; margin-top: 0; font-size: 20px;">{title}</h2>
                    <p style="color: #4b5563; font-size: 15px; line-height: 1.6;">{message}</p>
                    {f'<div style="margin-top: 24px;"><a href="{link}" style="display: inline-block; background: #35C98A; color: #ffffff; text-decoration: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; font-size: 14px;">View in SecondSpark &rarr;</a></div>' if link else ''}
                    <hr style="border: none; border-top: 1px solid #f3f4f6; margin: 28px 0 16px;" />
                    <p style="color: #9ca3af; font-size: 12px; margin: 0;">You received this notification because you are a registered maker on SecondSpark.</p>
                </div>
                """
                send_email_async(user.email, title, email_html)

        return notif
    except Exception as e:
        db.session.rollback()
        return None
