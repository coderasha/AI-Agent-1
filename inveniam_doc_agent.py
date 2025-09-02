import imaplib
import email
from email.header import decode_header
from pathlib import Path
import asyncio
import json


# -------- LOAD CONFIG ----------
with open("config.json") as f:
    cfg = json.load(f)

IMAP_SERVER = cfg["IMAP_SERVER"]
EMAIL_USER = cfg["EMAIL_USER"]
EMAIL_PASS = cfg["EMAIL_PASS"]

# Save inside Downloads/Inveniam-Docs
SAVE_DIR = Path.home() / "Downloads" / "Inveniam-Docs"
SAVE_DIR.mkdir(parents=True, exist_ok=True)


# -------- HELPERS ----------
def clean_filename(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name)


def save_pdf(filename, content):
    filepath = SAVE_DIR / filename
    with open(filepath, "wb") as f:
        f.write(content)
    print(f"✅ Saved: {filepath}")
    return str(filepath)


def process_email(raw_msg):
    msg = email.message_from_bytes(raw_msg)

    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding if encoding else "utf-8")

    print(f"\n📩 New email: {subject}")

    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get("Content-Disposition"):
            filename = part.get_filename()
            if filename and filename.lower().endswith(".pdf"):
                content = part.get_payload(decode=True)
                filename = clean_filename(filename)
                save_pdf(filename, content)


# -------- EMAIL LISTENER ----------
async def listen_inbox():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")

    print("🤖 Agent running... Listening for new emails...")

    while True:
        # Enter IDLE mode to wait for new messages
        mail.idle()
        print("... waiting for new mail ...")
        event = mail.idle_check(timeout=60)  # wait up to 60s
        mail.idle_done()

        if event and b"EXISTS" in event[0]:
            # Fetch unseen emails
            status, messages = mail.search(None, "UNSEEN")
            email_ids = messages[0].split()
            for eid in email_ids:
                res, msg_data = mail.fetch(eid, "(RFC822)")
                raw_msg = msg_data[0][1]
                process_email(raw_msg)

        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(listen_inbox())
