import os
import json
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv(override=True)

MEMORY_FILE = "memory/jarvis_memory.json"

class EmailSkill:
    def __init__(self):
        self.address = os.getenv("EMAIL_ADDRESS")
        self.password = os.getenv("EMAIL_PASSWORD")
        print("[EMAIL] Email module initialized.")

    def _resolve_email(self, name: str) -> str:
        """Returns an email address — either passed directly or looked up by name."""
        if "@" in name:
            return name
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r") as f:
                    data = json.load(f)
                contact = data.get("contacts", {}).get(name.lower(), {})
                if isinstance(contact, dict):
                    return contact.get("email", "")
            except Exception:
                pass
        return ""

    def send_email(self, to_name: str, subject: str, body: str) -> str:
        """Sends an email via Gmail SMTP."""
        if not self.address or not self.password:
            return (
                "Email credentials are not configured, sir. "
                "Add EMAIL_ADDRESS and EMAIL_PASSWORD to your .env file."
            )
        to_email = self._resolve_email(to_name)
        if not to_email:
            return f"I don't have an email address for {to_name}, sir."

        try:
            msg = MIMEMultipart()
            msg["From"] = self.address
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.address, self.password)
                server.sendmail(self.address, to_email, msg.as_string())

            return f"Email sent to {to_name}, sir."
        except Exception as e:
            print(f"[EMAIL] Send error: {e}")
            return f"I couldn't send the email, sir. {e}"

    def read_emails(self, count: int = 5) -> str:
        """Reads the latest N emails from your Gmail inbox."""
        if not self.address or not self.password:
            return "Email credentials are not configured, sir."
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.address, self.password)
            mail.select("inbox")

            _, data = mail.search(None, "ALL")
            ids = data[0].split()
            latest_ids = ids[-count:][::-1]

            summaries = []
            for uid in latest_ids:
                _, msg_data = mail.fetch(uid, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                subject = msg.get("Subject", "(no subject)")
                sender = msg.get("From", "unknown")
                summaries.append(f"{subject} from {sender}")

            mail.logout()

            if not summaries:
                return "Your inbox appears to be empty, sir."

            lines = [f"{i+1}: {s}" for i, s in enumerate(summaries)]
            return f"Your latest {len(summaries)} emails, sir. " + ". ".join(lines) + "."
        except Exception as e:
            print(f"[EMAIL] Read error: {e}")
            return f"I couldn't read your emails, sir. {e}"


if __name__ == "__main__":
    em = EmailSkill()
    print(em.read_emails(3))
