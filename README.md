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

## Public Deployment (Recommended: Render)

### Why Render?
- Easy UI for beginners
- Supports Flask web apps
- Managed PostgreSQL available
- Has Cron Jobs for reminder automation

### Deploy Architecture
1. Web Service (`gunicorn run:app`) for app UI/API
2. PostgreSQL database for persistent data
3. Cron Job (`python run_reminders.py`) for scheduled reminders

## Step-by-step (Exact)

### 1) Push project to GitHub
1. Create a new GitHub repo
2. Upload this project files

### 2) Create Render account
1. Open `https://render.com`
2. Sign up/login
3. Connect GitHub account

### 3) Create PostgreSQL on Render
1. Click `New +` -> `PostgreSQL`
2. Name: `expense-db` (any name)
3. Create database
4. Keep this page open (you will need connection URL)

### 4) Create Web Service
1. Click `New +` -> `Web Service`
2. Select your GitHub repo
3. Runtime: `Python`
4. Build Command:
   `pip install -r requirements.txt`
5. Start Command:
   `gunicorn run:app`
6. Add env vars:
- `SECRET_KEY` = any random long text
- `DATABASE_URL` = Render PostgreSQL Internal Database URL
- `SMTP_HOST=smtp.gmail.com`
- `SMTP_PORT=587`
- `SMTP_USER=yourgmail@gmail.com`
- `SMTP_PASS=your_gmail_app_password`
- `MAIL_FROM=yourgmail@gmail.com`
- `SMTP_USE_TLS=1`
- `SMTP_USE_SSL=0`
- `ENABLE_SCHEDULER=0`
7. Click `Create Web Service`

### 5) Create Cron Job for reminders
1. Click `New +` -> `Cron Job`
2. Select same repo
3. Build Command:
   `pip install -r requirements.txt`
4. Start Command:
   `python run_reminders.py`
5. Schedule: every 1 hour
6. Add same env vars as Web Service
7. Click `Create Cron Job`

### 6) Open your public app
- Use your Render Web Service URL
- Anyone can access it

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
