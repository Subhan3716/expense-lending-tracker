import smtplib
from email.message import EmailMessage

from flask import current_app


def send_reminder_email(record):
    host = current_app.config.get("SMTP_HOST", "")
    port = current_app.config.get("SMTP_PORT", 587)
    username = current_app.config.get("SMTP_USER", "")
    password = current_app.config.get("SMTP_PASS", "")
    sender = current_app.config.get("MAIL_FROM", "")
    use_tls = current_app.config.get("SMTP_USE_TLS", True)
    use_ssl = current_app.config.get("SMTP_USE_SSL", False)

    if not all([host, port, sender]):
        reason = "SMTP_HOST/SMTP_PORT/MAIL_FROM missing"
        current_app.logger.warning(
            "SMTP config missing. Skipping reminder email for record id=%s", record.id
        )
        return False, reason

    due_time_text = record.due_time.strftime("%H:%M") if record.due_time else "09:00"

    note_block = ""
    if record.note and record.note.strip():
        note_block = f"Note: {record.note.strip()}\n"

    message = EmailMessage()
    message["Subject"] = "Payment Reminder - Expense Tracker"
    message["From"] = sender
    message["To"] = record.email
    message.set_content(
        (
            f"Hello {record.person_name},\n\n"
            "Friendly reminder: your payment is still pending.\n"
            f"Amount: {record.amount}\n"
            f"Due: {record.due_date.strftime('%Y-%m-%d')} {due_time_text}\n"
            f"{note_block}\n"
            "Please clear it as soon as possible.\n\n"
            "Thank you."
        ),
        charset="utf-8",
    )

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
                if username and password:
                    smtp.login(username, password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=30) as smtp:
                smtp.ehlo()
                if use_tls:
                    smtp.starttls()
                    smtp.ehlo()
                if username and password:
                    smtp.login(username, password)
                smtp.send_message(message)

        return True, None
    except Exception as exc:
        current_app.logger.exception(
            "Failed to send reminder email for record id=%s", record.id
        )
        return False, str(exc)
