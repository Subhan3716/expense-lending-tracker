import os
from datetime import datetime, time

from apscheduler.triggers.interval import IntervalTrigger

from .extensions import db, scheduler
from .mailer import send_reminder_email
from .models import LentRecord


def _is_due_for_reminder(record, now):
    if record.status != LentRecord.STATUS_UNPAID:
        return False

    if now < record.due_datetime:
        return False

    today = now.date()
    if record.last_reminder_date == today:
        return False

    due_time = record.due_time or time(9, 0)

    # After first reminder, send from due-time onward each next day.
    if record.last_reminder_date is not None and now.time() < due_time:
        return False

    return True


def run_due_reminders(app):
    with app.app_context():
        now = datetime.now()
        unpaid_records = LentRecord.query.filter(
            LentRecord.status == LentRecord.STATUS_UNPAID
        ).all()

        sent_count = 0
        for record in unpaid_records:
            if not _is_due_for_reminder(record, now):
                continue

            sent, error = send_reminder_email(record)
            if sent:
                record.last_reminder_date = now.date()
                record.reminder_sent_at = datetime.utcnow()
                sent_count += 1
            else:
                app.logger.warning(
                    "Reminder send failed for record id=%s. %s", record.id, error
                )

        if sent_count:
            db.session.commit()
            app.logger.info("Sent %s payment reminder email(s).", sent_count)

        return sent_count


def start_scheduler(app):
    if scheduler.running:
        return

    # Flask debug reloader starts the app twice. Start scheduler only in reloader child.
    debug_enabled = app.debug or os.getenv("FLASK_DEBUG") == "1"
    if debug_enabled and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    interval_hours = app.config.get("REMINDER_INTERVAL_HOURS", 1)
    scheduler.add_job(
        func=run_due_reminders,
        trigger=IntervalTrigger(hours=interval_hours),
        args=[app],
        id="send_due_payment_reminders",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        next_run_time=datetime.utcnow(),
    )
    scheduler.start()
