import atexit
import os
from decimal import Decimal

from dotenv import load_dotenv
from flask import Flask
from sqlalchemy import inspect, text

from .extensions import db, scheduler
from .reminders import start_scheduler
from .routes import main_bp


def currency(value):
    try:
        return f"{Decimal(value):,.2f}"
    except Exception:
        return "0.00"


def _as_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _normalized_database_url(raw_url):
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+psycopg://", 1)
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw_url


def create_app():
    load_dotenv()

    instance_path = None
    if os.getenv("VERCEL"):
        instance_path = os.path.join("/tmp", "instance")

    if instance_path:
        app = Flask(
            __name__,
            instance_relative_config=True,
            instance_path=instance_path,
        )
    else:
        app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-me")

    raw_db_url = os.getenv("DATABASE_URL", "sqlite:///expense_lending.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = _normalized_database_url(raw_db_url)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["SMTP_HOST"] = os.getenv("SMTP_HOST", "")
    app.config["SMTP_PORT"] = int(os.getenv("SMTP_PORT", "587"))
    app.config["SMTP_USER"] = os.getenv("SMTP_USER", "")
    app.config["SMTP_PASS"] = os.getenv("SMTP_PASS", "")
    app.config["MAIL_FROM"] = os.getenv("MAIL_FROM", os.getenv("SMTP_USER", ""))
    app.config["SMTP_USE_TLS"] = _as_bool(os.getenv("SMTP_USE_TLS", "1"), default=True)
    app.config["SMTP_USE_SSL"] = _as_bool(os.getenv("SMTP_USE_SSL", "0"), default=False)

    app.config["REMINDER_INTERVAL_HOURS"] = int(os.getenv("REMINDER_INTERVAL_HOURS", "1"))
    app.config["ENABLE_SCHEDULER"] = _as_bool(os.getenv("ENABLE_SCHEDULER", "1"), True)

    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        # Vercel serverless filesystem can be read-only in /var/task.
        pass

    db.init_app(app)
    app.register_blueprint(main_bp)
    app.jinja_env.filters["currency"] = currency

    with app.app_context():
        db.create_all()
        _ensure_schema_compatibility()

    if app.config["ENABLE_SCHEDULER"]:
        start_scheduler(app)
        atexit.register(_safe_scheduler_shutdown)

    return app


def _ensure_schema_compatibility():
    inspector = inspect(db.engine)
    if "lent_records" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("lent_records")}
    if "due_time" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE lent_records "
                "ADD COLUMN due_time TIME NOT NULL DEFAULT '09:00:00'"
            )
        )
        db.session.commit()


def _safe_scheduler_shutdown():
    if scheduler.running:
        scheduler.shutdown(wait=False)
