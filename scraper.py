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
BASE_URL         = "https://disneyworld.disney.go.com"
# -------------------------------------------------------------------


def fetch_events():
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(URL, headers=headers, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    events = []

    # Find the Merchandise Spotlight section
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
            break

        for h3 in sibling.find_all("h3") if sibling.name != "h3" else [sibling]:
            title_raw = h3.get_text(strip=True)
            if not title_raw:
                continue

            # Check for SOLD OUT in the surrounding block
            parent = h3.find_parent()
            parent_text = parent.get_text(separator="\n", strip=True) if parent else ""
            sold_out = "SOLD OUT" in parent_text.upper()

            # Pull date/time/location details
            details = {}
            for line in parent_text.split("\n"):
                line = line.strip()
                if line.lower().startswith("date"):
                    details["date"] = line
                elif line.lower().startswith("time"):
                    details["time"] = line
                elif line.lower().startswith("location"):
                    details["location"] = line

            # Look for any registration/ticket/buy links nearby
            registration_link = None
            if parent:
                for a in parent.find_all("a", href=True):
                    href = a["href"]
                    link_text = a.get_text(strip=True).lower()
                    if any(word in link_text for word in ["register", "ticket", "buy", "purchase", "book", "reserve"]):
                        registration_link = BASE_URL + href if href.startswith("/") else href
                        break
                    if any(word in href for word in ["ticket", "register", "book", "purchase"]):
                        registration_link = BASE_URL + href if href.startswith("/") else href
                        break

            # Clean up title
            title = title_raw.replace("SOLD OUT", "").strip()

            events.append({
                "title": title,
                "sold_out": sold_out,
                "registration_link": registration_link,
                "details": details
            })

    return events


def load_seen_events():
    if os.path.exists(SEEN_EVENTS_FILE):
        with open(SEEN_EVENTS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_seen_events(events_dict):
    with open(SEEN_EVENTS_FILE, "w") as f:
        json.dump(events_dict, f, indent=2)


def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = EMAIL_RECIPIENT
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())

    print(f"Email sent: {subject}")


def format_event(event):
    lines = [f">> {event['title']}"]
    if event.get("sold_out"):
        lines.append("   STATUS: SOLD OUT")
    for v in event.get("details", {}).values():
        lines.append(f"   {v}")
    if event.get("registration_link"):
        lines.append(f"   LINK: {event['registration_link']}")
    return "\n".join(lines)


def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Checking for updates...")

    current_events = fetch_events()
    seen = load_seen_events()

    alerts = []

    for event in current_events:
        title = event["title"]
        prev  = seen.get(title)

        if prev is None:
            # Brand new event
            alerts.append(f"NEW EVENT FOUND:\n{format_event(event)}")

        else:
            # Registration link just appeared
            if not prev.get("registration_link") and event.get("registration_link"):
                alerts.append(
                    f"REGISTRATION LINK NOW LIVE for: {title}\n"
                    f"   Link: {event['registration_link']}\n"
                    + "\n".join(f"   {v}" for v in event.get("details", {}).values())
                )

            # Sold out status changed
            if not prev.get("sold_out") and event.get("sold_out"):
                alerts.append(f"NOW SOLD OUT: {title}")

            if prev.get("sold_out") and not event.get("sold_out"):
                alerts.append(f"NO LONGER SOLD OUT (tickets may be available again!): {title}")

    if alerts:
        subject = f"[magic-cherry] Disney Merchandise Alert -- {len(alerts)} update(s)"
        body = f"Updates found on the Disney World Merchandise Spotlight page as of {datetime.now().strftime('%B %d, %Y %I:%M %p')}:\n\n"
        body += "\n\n".join(alerts)
        body += f"\n\nView the full page: {URL}"
        print(body)
        send_email(subject, body)
    else:
        print("No changes found.")

    # Save current state keyed by title
    new_seen = {e["title"]: e for e in current_events}
    save_seen_events(new_seen)


if __name__ == "__main__":
    main()
