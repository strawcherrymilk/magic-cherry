# magic-cherry setup

## Requirements
- Python 3.8+
- A Gmail account with an App Password

---

## 1. Install dependencies

```
pip install -r requirements.txt
```

---

## 2. Configure the script

Open `scraper.py` and fill in the CONFIG block at the top:

```python
EMAIL_SENDER    = "your_gmail@gmail.com"
EMAIL_PASSWORD  = "your_app_password"     # see below
EMAIL_RECIPIENT = "your_email@example.com"
```

### Getting a Gmail App Password
Gmail requires an App Password (not your real password) for scripts:
1. Go to your Google Account > Security
2. Enable 2-Step Verification if not already on
3. Go to Security > App Passwords
4. Create one, name it anything (e.g. "magic-cherry")
5. Paste the generated 16-character password into EMAIL_PASSWORD

---

## 3. Test it manually

```
python scraper.py
```

First run: saves all current events to `seen_events.json`, no email sent unless events are new.
Subsequent runs: emails you only if a new event title appears.

---

## 4. Schedule it (runs daily)

### Mac/Linux (cron)
```
crontab -e
```
Add this line to run every day at 9am:
```
0 9 * * * /usr/bin/python3 /path/to/magic-cherry/scraper.py >> /path/to/magic-cherry/scraper.log 2>&1
```

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily
4. Action: Start a program
   - Program: `python`
   - Arguments: `C:\path\to\magic-cherry\scraper.py`

---

## How it works
- Scrapes the Merchandise Spotlight section of the Disney shopping events page
- Compares event titles against `seen_events.json`
- Emails you only when a new event title appears
- Updates `seen_events.json` after each run
