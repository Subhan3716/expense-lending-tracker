import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func

from .extensions import db
from .mailer import send_reminder_email
from .models import Expense, LentRecord


main_bp = Blueprint("main", __name__)
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def _parse_time(value):
    return datetime.strptime(value, "%H:%M").time()


def _parse_positive_amount(value):
    amount = Decimal(value)
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    return amount


def _is_overdue(record, now=None):
    now = now or datetime.now()
    return record.status == LentRecord.STATUS_UNPAID and now >= record.due_datetime


@main_bp.route("/")
def dashboard():
    now = datetime.now()
    today = now.date()
    month_start = today.replace(day=1)

    today_total = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(Expense.expense_date == today)
        .scalar()
    )
    month_total = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(Expense.expense_date >= month_start, Expense.expense_date <= today)
        .scalar()
    )

    category_totals = (
        db.session.query(Expense.category, func.sum(Expense.amount).label("total"))
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )

    pending_lending_total = (
        db.session.query(func.coalesce(func.sum(LentRecord.amount), 0))
        .filter(LentRecord.status == LentRecord.STATUS_UNPAID)
        .scalar()
    )

    unpaid_records = LentRecord.query.filter(
        LentRecord.status == LentRecord.STATUS_UNPAID
    ).all()
    overdue_count = sum(1 for record in unpaid_records if _is_overdue(record, now=now))

    recent_lending = LentRecord.query.order_by(
        LentRecord.created_at.desc()
    ).limit(5).all()

    return render_template(
        "dashboard.html",
        today=today,
        now=now,
        today_total=today_total,
        month_total=month_total,
        category_totals=category_totals,
        pending_lending_total=pending_lending_total,
        overdue_count=overdue_count,
        recent_lending=recent_lending,
    )


@main_bp.route("/expenses", methods=["GET", "POST"])
def expenses():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        amount_input = request.form.get("amount", "").strip()
        expense_date_input = request.form.get("expense_date", "").strip()
        note = request.form.get("note", "").strip()

        if not title or not category or not amount_input or not expense_date_input:
            flash("Please fill all required expense fields.", "danger")
            return redirect(url_for("main.expenses"))

        try:
            amount = _parse_positive_amount(amount_input)
            expense_date = _parse_date(expense_date_input)
        except (InvalidOperation, ValueError):
            flash("Enter a valid positive amount and date.", "danger")
            return redirect(url_for("main.expenses"))

        expense = Expense(
            title=title,
            category=category,
            amount=amount,
            expense_date=expense_date,
            note=note or None,
        )
        db.session.add(expense)
        db.session.commit()
        flash("Expense added successfully.", "success")
        return redirect(url_for("main.expenses"))

    all_expenses = Expense.query.order_by(
        Expense.expense_date.desc(), Expense.id.desc()
    ).all()
    return render_template("expenses.html", expenses=all_expenses, today=date.today())


@main_bp.post("/expenses/delete/<int:expense_id>")
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted.", "success")
    return redirect(url_for("main.expenses"))


@main_bp.route("/lending", methods=["GET", "POST"])
def lending():
    now = datetime.now()
    if request.method == "POST":
        person_name = request.form.get("person_name", "").strip()
        email = request.form.get("email", "").strip()
        amount_input = request.form.get("amount", "").strip()
        lent_date_input = request.form.get("lent_date", "").strip()
        due_date_input = request.form.get("due_date", "").strip()
        due_time_input = request.form.get("due_time", "").strip()
        note = request.form.get("note", "").strip()

        if not all([
            person_name,
            email,
            amount_input,
            lent_date_input,
            due_date_input,
            due_time_input,
        ]):
            flash("Please fill all required lending fields.", "danger")
            return redirect(url_for("main.lending"))

        if not EMAIL_REGEX.match(email):
            flash("Please enter a valid borrower email address.", "danger")
            return redirect(url_for("main.lending"))

        try:
            amount = _parse_positive_amount(amount_input)
            lent_date = _parse_date(lent_date_input)
            due_date = _parse_date(due_date_input)
            due_time = _parse_time(due_time_input)
        except (InvalidOperation, ValueError):
            flash("Enter valid dates/time and a positive amount.", "danger")
            return redirect(url_for("main.lending"))

        if due_date < lent_date:
            flash("Due date must be on or after lent date.", "danger")
            return redirect(url_for("main.lending"))

        record = LentRecord(
            person_name=person_name,
            email=email,
            amount=amount,
            lent_date=lent_date,
            due_date=due_date,
            due_time=due_time,
            status=LentRecord.STATUS_UNPAID,
            note=note or None,
        )
        db.session.add(record)
        db.session.commit()
        flash("Lending record saved.", "success")
        return redirect(url_for("main.lending"))

    lending_records = LentRecord.query.order_by(
        LentRecord.due_date.asc(), LentRecord.due_time.asc(), LentRecord.id.desc()
    ).all()
    return render_template(
        "lending.html",
        records=lending_records,
        today=now.date(),
        now=now,
    )


@main_bp.post("/lending/send-reminder/<int:record_id>")
def send_reminder_now(record_id):
    record = LentRecord.query.get_or_404(record_id)

    if record.status == LentRecord.STATUS_PAID:
        flash("This record is already paid. No reminder sent.", "warning")
        return redirect(url_for("main.lending"))

    sent, error = send_reminder_email(record)
    if sent:
        record.last_reminder_date = date.today()
        record.reminder_sent_at = datetime.utcnow()
        db.session.commit()
        flash(f"Reminder sent to {record.email}.", "success")
    else:
        flash(
            "Reminder failed. Check SMTP settings in .env or terminal logs. "
            f"Error: {error}",
            "danger",
        )

    return redirect(url_for("main.lending"))


@main_bp.post("/lending/mark-paid/<int:record_id>")
def mark_paid(record_id):
    record = LentRecord.query.get_or_404(record_id)
    record.status = LentRecord.STATUS_PAID
    db.session.commit()
    flash("Record marked as paid. Daily reminders stopped.", "success")
    return redirect(url_for("main.lending"))


@main_bp.post("/lending/delete/<int:record_id>")
def delete_lending(record_id):
    record = LentRecord.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    flash("Lending record deleted.", "success")
    return redirect(url_for("main.lending"))
