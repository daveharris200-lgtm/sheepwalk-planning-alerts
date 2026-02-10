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


def get_page_state():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL, timeout=60000)
        page.wait_for_load_state("networkidle")

        # Status
        status = page.locator("text=Status").locator("xpath=../td[2]").inner_text()

        # Decision (may be blank)
        decision = ""
        if page.locator("text=Decision").count() > 0:
            decision = page.locator("text=Decision").locator("xpath=../td[2]").inner_text()

        # Documents
        documents = page.locator("a[href*='downloadDocument']").all_inner_texts()

        browser.close()

        return {
            "status": status.strip(),
            "decision": decision.strip(),
            "documents": sorted([d.strip() for d in documents])
        }


def load_previous():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return None


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def detect_changes(old, new):
    changes = []

    if old["status"] != new["status"]:
        changes.append(f"Status changed: {old['status']} → {new['status']}")

    if old.get("decision") != new.get("decision") and new.get("decision"):
        changes.append(f"Decision issued: {new['decision']}")

    new_docs = set(new["documents"]) - set(old["documents"])
    if new_docs:
        changes.append(f"{len(new_docs)} new document(s) added")

    return changes


def send_email(changes, state):
    body = f"""
Planning application update: {APP_REF}

Changes detected:
- """ + "\n- ".join(changes) + f"""

Current status: {state['status']}
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
    changes = detect_changes(previous, current)
    if changes:
        send_email(changes, current)

save_state(current)
