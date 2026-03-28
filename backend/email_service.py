from __future__ import annotations
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config import settings
from backend.logger import get_logger

logger = get_logger(__name__)


def send_lead_notification(
    lead_name: str,
    lead_email: str,
    lead_phone: str = "",
    interest: str = "",
    message: str = "",
) -> bool:
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.info("Email not configured, skipping notification")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Novy lead: {lead_name} — FinAdvisor SK"
        msg["From"] = settings.SMTP_USER
        msg["To"] = settings.NOTIFY_EMAIL
        html = f"""
        <h2>Novy lead na finadvisor.sk</h2>
        <p><b>Meno:</b> {lead_name}</p>
        <p><b>Email:</b> {lead_email}</p>
        <p><b>Telefon:</b> {lead_phone or '—'}</p>
        <p><b>Oblast:</b> {interest or '—'}</p>
        <p><b>Sprava:</b> {message or '—'}</p>
        <hr/>
        <p><a href="https://finadvisor.sk/admin">Otvorit admin panel</a></p>
        """
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, settings.NOTIFY_EMAIL, msg.as_string())
        logger.info("Lead notification sent to %s", settings.NOTIFY_EMAIL)
        return True
    except Exception as e:
        logger.warning("Failed to send email: %s", e)
        return False
