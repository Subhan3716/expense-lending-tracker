from datetime import datetime, time

from .extensions import db


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    expense_date = db.Column(db.Date, nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class LentRecord(db.Model):
    __tablename__ = "lent_records"

    STATUS_UNPAID = "UNPAID"
    STATUS_PAID = "PAID"

    id = db.Column(db.Integer, primary_key=True)
    person_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    lent_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    due_time = db.Column(db.Time, nullable=False, default=lambda: time(9, 0))
    status = db.Column(db.String(20), nullable=False, default=STATUS_UNPAID)
    note = db.Column(db.Text, nullable=True)
    reminder_sent_at = db.Column(db.DateTime, nullable=True)
    last_reminder_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def due_datetime(self):
        return datetime.combine(self.due_date, self.due_time or time(9, 0))

    @property
    def is_overdue(self):
        return self.status == self.STATUS_UNPAID and datetime.now() >= self.due_datetime
