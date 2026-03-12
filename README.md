# Smart Expense & Lending Tracker

Full-stack Flask app for:
- Expense tracking
- Lending/borrower tracking
- Due date+time reminders by email
- Emoji notes support

## Local Run
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```
Open: `http://127.0.0.1:5000`

## Public Deployment (Vercel)

### Deploy Architecture
1. Vercel web app for UI/API
2. External PostgreSQL database (Neon is free)
3. Daily Cron on Vercel to call `/api/cron`

### 1) Push project to GitHub
1. Create a new GitHub repo
2. Upload this project files

### 2) Create PostgreSQL on Neon
1. Open `https://neon.tech`
2. Create a free project
3. Copy the `DATABASE_URL` (it starts with `postgresql://`)

### 3) Create Vercel project
1. Open `https://vercel.com`
2. Import your GitHub repo
3. Deploy

### 4) Add environment variables in Vercel
Add these variables in Vercel project settings:
- `SECRET_KEY` = any random long text
- `DATABASE_URL` = Neon `DATABASE_URL`
- `SMTP_HOST=smtp.gmail.com`
- `SMTP_PORT=587`
- `SMTP_USER=yourgmail@gmail.com`
- `SMTP_PASS=your_gmail_app_password`
- `MAIL_FROM=yourgmail@gmail.com`
- `SMTP_USE_TLS=1`
- `SMTP_USE_SSL=0`
- `ENABLE_SCHEDULER=0`

### 5) Cron schedule
The repo includes `vercel.json` with a daily cron that calls `/api/cron`:
```json
{
  "crons": [
    { "path": "/api/cron", "schedule": "0 0 * * *" }
  ]
}
```
Cron schedules are in UTC and run once per day on the free plan.

## Important Production Notes
- Never use SQLite in cloud deployment. Use PostgreSQL (`DATABASE_URL`).
- Never paste normal Gmail password. Use Gmail App Password.
- Rotate password/app-password if it was shared publicly.

## Files used for deployment
- `run.py` (Flask app entry)
- `run_reminders.py` (one-time reminder runner for cron)
- `requirements.txt` (dependencies)
- `runtime.txt` (Python runtime)
- `app/__init__.py` (DB URL normalization + scheduler toggle)
