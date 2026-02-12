import json
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from playwright.sync_api import sync_playwright

# ---------------- CONFIG ----------------
URL = "https://publicaccess.huntingdonshire.gov.uk/online-applications/applicationDetails.do?activeTab=summary&keyVal=T07XB4IKGTL00"
APP_REF = "25/01436/FUL"

EMAIL_TO = "daveharris200@gmail.com"
EMAIL_FROM = "planning.agent@gmail.com"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

STATE_FILE = Path("last_state.json")
# ---------------------------------------

import json
import os


STATE_FILE = "last_state.json"


def load_previous():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return None


def save_current(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def safe_text(page, label):
    try:
        return (
            page.locator(f"text={label}")
            .first
            .locator("xpath=../../td[last()]")
            .inner_text(timeout=5000)
            .strip()
        )
    except:
        return None


def get_page_state():
    from playwright.sync_api import sync_playwright

    URL = "https://publicaccess.huntingdonshire.gov.uk/online-applications/applicationDetails.do?activeTab=summary&keyVal=T07XB4IKGTL00"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(URL, timeout=60000)
        page.wait_for_timeout(3000)

        status = safe_text(page, "Status")
        decision = safe_text(page, "Decision")
        comment_deadline = safe_text(page, "Comments by")

        docs = page.locator("a[href*='downloadDocument']")
        documents = []
        for i in range(docs.count()):
            documents.append({
                "name": docs.nth(i).inner_text().strip(),
                "url": docs.nth(i).get_attribute("href")
            })

        browser.close()

        return {
            "status": status,
            "decision": decision,
            "comment_deadline": comment_deadline,
            "documents": documents
        }


def send_email(changes, current_state, decision_alert=False, heartbeat=False):

    body = f"""
subject = f"Planning update – {APP_REF}"

if decision_alert:
    subject = f"🚨 DECISION ISSUED – {APP_REF}"
elif heartbeat:
    subject = f"Heartbeat – {APP_REF}"

Changes detected:
- """ + "\n- ".join(changes) + f"""

current_state['status']
current_state['decision']
current_state['comment_deadline']

Decision: {state.get('decision', '—')}

This email was sent automatically.
"""

    msg = MIMEText(body)
    msg["Subject"] = f"Planning update – {APP_REF}"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_FROM, SMTP_PASSWORD)
        server.send_message(msg)


# ---------------- RUN ----------------
current = get_page_state()
previous = load_previous()

if previous:
    changes, decision_alert = detect_changes(previous, current)

    if changes:
        send_email(changes, decision_alert)
    else:
        # Daily heartbeat
        send_email(
            ["No changes detected today."],
            decision_alert=False,
            heartbeat=True
        )
else:
    # First run – initialise state
    save_current(current)
    send_email(
        ["Monitoring started. No previous state to compare yet."],
        decision_alert=False,
        heartbeat=True
    )

save_current(current)



import json
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from playwright.sync_api import sync_playwright

# ---------------- CONFIG ----------------
URL = "https://publicaccess.huntingdonshire.gov.uk/online-applications/applicationDetails.do?activeTab=summary&keyVal=T07XB4IKGTL00"
APP_REF = "25/01436/FUL"

EMAIL_TO = "daveharris200@gmail.com"
EMAIL_FROM = "planning.agent@gmail.com"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

STATE_FILE = Path("last_state.json")
# ---------------------------------------

import json
import os


STATE_FILE = "last_state.json"


def load_previous():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return None


def save_current(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def safe_text(page, label):
    try:
        return (
            page.locator(f"text={label}")
            .first
            .locator("xpath=../../td[last()]")
            .inner_text(timeout=5000)
            .strip()
        )
    except:
        return None


def get_page_state():
    from playwright.sync_api import sync_playwright

    URL = "https://publicaccess.huntingdonshire.gov.uk/online-applications/applicationDetails.do?activeTab=summary&keyVal=T07XB4IKGTL00"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(URL, timeout=60000)
        page.wait_for_timeout(3000)

        status = safe_text(page, "Status")
        decision = safe_text(page, "Decision")
        comment_deadline = safe_text(page, "Comments by")

        docs = page.locator("a[href*='downloadDocument']")
        documents = []
        for i in range(docs.count()):
            documents.append({
                "name": docs.nth(i).inner_text().strip(),
                "url": docs.nth(i).get_attribute("href")
            })

        browser.close()

        return {
            "status": status,
            "decision": decision,
            "comment_deadline": comment_deadline,
            "documents": documents
        }


def send_email(changes, current_state, decision_alert=False, heartbeat=False):

    body = f"""
subject = f"Planning update – {APP_REF}"

if decision_alert:
    subject = f"🚨 DECISION ISSUED – {APP_REF}"
elif heartbeat:
    subject = f"Heartbeat – {APP_REF}"

Changes detected:
- """ + "\n- ".join(changes) + f"""

Current status: {current_state['status']}
Decision: {state.get('decision', '—')}

This email was sent automatically.
"""

    msg = MIMEText(body)
    msg["Subject"] = f"Planning update – {APP_REF}"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_FROM, SMTP_PASSWORD)
        server.send_message(msg)


# ---------------- RUN ----------------
current = get_page_state()
previous = load_previous()

if previous:
    changes, decision_alert = detect_changes(previous, current)

    if changes:
        send_email(changes, current, decision_alert)
    else:
        # Daily heartbeat    
        send_email(
    ["No changes detected today."],
    current,
    decision_alert=False,
    heartbeat=True
)
    
        )
else:
    # First run – initialise state
    save_current(current)
    send_email(
    ["Monitoring started. No previous state to compare yet."],
    current,
    decision_alert=False,
    heartbeat=True
)

save_current(current)



