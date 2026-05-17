import requests
from bs4 import BeautifulSoup
import json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# -------------------------------------------------------------------
# CONFIG -- fill these in before running
# -------------------------------------------------------------------
EMAIL_SENDER     = "hausoftaeyong@gmail.com"
EMAIL_PASSWORD   = "qtoh xxeo sdbt alrk"       # Gmail App Password, not your real password
EMAIL_RECIPIENT  = "hausoftaeyong@gmail.com"
SEEN_EVENTS_FILE = "seen_events.json"
URL              = "https://disneyworld.disney.go.com/events-tours/shopping-events/"
# -------------------------------------------------------------------


def fetch_events():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    events = []

    # Find the Merchandise Spotlight section
    # It's identified by the h2 heading on the page
    spotlight_heading = None
    for h2 in soup.find_all("h2"):
        if "Merchandise Spotlight" in h2.get_text():
            spotlight_heading = h2
            break

    if not spotlight_heading:
        print("Could not find Merchandise Spotlight section.")
        return events

    # Walk siblings until the next h2 (next section)
    for sibling in spotlight_heading.find_next_siblings():
        if sibling.name == "h2":
            break  # stop at next section

        # Event titles are in h3 tags
        for h3 in sibling.find_all("h3") if sibling.name != "h3" else [sibling]:
            title = h3.get_text(strip=True)
            if not title:
                continue

            # Try to find date/location nearby
            details = {}
            parent = h3.find_parent()
            if parent:
                text = parent.get_text(separator="\n", strip=True)
                for line in text.split("\n"):
                    line = line.strip()
                    if line.lower().startswith("date"):
                        details["date"] = line
                    elif line.lower().startswith("time"):
                        details["time"] = line
                    elif line.lower().startswith("location"):
                        details["location"] = line

            events.append({"title": title, "details": details})

    return events


def load_seen_events():
    if os.path.exists(SEEN_EVENTS_FILE):
        with open(SEEN_EVENTS_FILE, "r") as f:
            return json.load(f)
    return []


def save_seen_events(events):
    with open(SEEN_EVENTS_FILE, "w") as f:
        json.dump(events, f, indent=2)


def send_email(new_events):
    subject = f"[magic-cherry] {len(new_events)} New Disney Merchandise Event(s) Found"

    body_lines = [
        f"New events found on the Disney World Merchandise Spotlight page as of {datetime.now().strftime('%B %d, %Y')}:\n"
    ]

    for event in new_events:
        body_lines.append(f"-- {event['title']}")
        for k, v in event.get("details", {}).items():
            body_lines.append(f"   {v}")
        body_lines.append("")

    body_lines.append(f"View the full page: {URL}")
    body = "\n".join(body_lines)

    msg = MIMEMultipart()
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = EMAIL_RECIPIENT
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())

    print(f"Email sent: {subject}")


def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Checking for new events...")

    current_events  = fetch_events()
    seen_titles     = load_seen_events()
    current_titles  = [e["title"] for e in current_events]

    new_events = [e for e in current_events if e["title"] not in seen_titles]

    if new_events:
        print(f"Found {len(new_events)} new event(s):")
        for e in new_events:
            print(f"  - {e['title']}")
        send_email(new_events)
        save_seen_events(current_titles)
    else:
        print("No new events found.")
        # Still update the seen list in case events were removed
        save_seen_events(current_titles)


if __name__ == "__main__":
    main()
