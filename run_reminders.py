from app import create_app
from app.reminders import run_due_reminders


if __name__ == "__main__":
    app = create_app()
    sent = run_due_reminders(app)
    print(f"Reminder run completed. Emails sent: {sent}")
