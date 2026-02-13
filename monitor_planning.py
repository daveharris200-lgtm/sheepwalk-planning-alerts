import json
import os
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

# ---------------- CONFIG ----------------
URL = "https://publicaccess.huntingdonshire.gov.uk/online-applications/applicationDetails.do?activeTab=summary&keyVal=T07XB4IKGTL00"
APP_REF = "25/01436/FUL"

EMAIL_TO = "daveharris200@gmail.com"
EMAIL_FROM = os.environ["EMAIL_USER"]
SMTP_PASSWORD = os.environ["EMAIL_PASS"]

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

STATE_FILE = "last_state.json"
# ---------------------------------------


# -------- STATE HANDLING --------
def load_previous():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return None


def save_current(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# -------- PAGE SCRAPING --------
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


# -------- CHANGE DETECTION --------
def detect_changes(old, new):
    changes = []
    decision_alert = False

    if old.get("status") != new.get("status"):
        changes.append(f"Status changed: {old.get('status')} → {new.get('status')}")

    if not old.get("decision") and new.get("decision"):
        decision_alert = True
        changes.append(f"🚨 DECISION ISSUED: {new.get('decision')}")

    old_docs = {d["name"] for d in old.get("documents", [])}
    new_docs = [d for d in new.get("documents", []) if d["name"] not in old_docs]

    for doc in new_docs:
        changes.append(f"New document: {doc['name']} — {doc['url']}")

    return changes, decision_alert


# -------- EMAIL --------
def send_email(changes, current_state, decision_alert=False, heartbeat=False):
    subject = f"Planning update – {APP_REF}"

    if decision_alert:
        subject = f"🚨 DECISION ISSUED – {APP_REF}"
    elif heartbeat:
        subject = f"Heartbeat – {APP_REF}"

    body_lines = [
        f"Planning application update: {APP_REF}",
        "",
    ]

    body_lines.extend(changes)

    body_lines.extend([
        "",
        f"Current status: {current_state.get('status', '—')}",
        f"Decision: {current_state.get('decision', '—')}",
        f"Comment deadline: {current_state.get('comment_deadline', '—')}",
        "",
        "This email was sent automatically."
    ])

    body = "\n".join(body_lines)

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(EMAIL_FROM, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Email failed: {e}")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_FROM, SMTP_PASSWORD)
        server.send_message(msg)


# -------- RUN --------
current = get_page_state()
previous = load_previous()

if previous:
    changes, decision_alert = detect_changes(previous, current)

    if changes:
        send_email(changes, current, decision_alert)
    else:
        send_email(
            ["No changes detected today."],
            current,
            decision_alert=False,
            heartbeat=True
        )
else:
    save_current(current)
    send_email(
        ["Monitoring started. No previous state to compare yet."],
        current,
        decision_alert=False,
        heartbeat=True
    )

save_current(current)
