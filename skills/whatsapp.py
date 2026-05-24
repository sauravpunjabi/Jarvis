import os
import json

MEMORY_FILE = "memory/jarvis_memory.json"

class WhatsAppSkill:
    def __init__(self):
        print("[WHATSAPP] WhatsApp module initialized.")

    def _load_contacts(self) -> dict:
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r") as f:
                    return json.load(f).get("contacts", {})
            except Exception:
                pass
        return {}

    def _save_contact_to_memory(self, name: str, phone: str):
        data = {}
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r") as f:
                    data = json.load(f)
            except Exception:
                pass
        data.setdefault("contacts", {})[name.lower()] = {"phone": phone}
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        with open(MEMORY_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def add_contact(self, name: str, phone: str) -> str:
        """Saves a contact name and phone number to memory."""
        self._save_contact_to_memory(name, phone)
        return f"Contact saved — {name} at {phone}, sir."

    def send_whatsapp(self, contact_name: str, message: str) -> str:
        """Sends a WhatsApp message to a saved contact."""
        contacts = self._load_contacts()
        name_key = contact_name.lower().strip()
        contact = contacts.get(name_key, {})

        # Support both {phone: ...} dict and legacy plain string
        phone = contact.get("phone") if isinstance(contact, dict) else contact
        if not phone:
            return (
                f"I don't have a number for {contact_name}, sir. "
                f"Say 'add contact {contact_name}' to save their number."
            )

        try:
            import pywhatkit
            pywhatkit.sendwhatmsg_instantly(phone, message, wait_time=15, tab_close=True)
            return f"Message sent to {contact_name}, sir."
        except ImportError:
            return "pywhatkit is not installed, sir. Run: pip install pywhatkit"
        except Exception as e:
            print(f"[WHATSAPP] Error: {e}")
            return f"Failed to send the message to {contact_name}, sir."


if __name__ == "__main__":
    wa = WhatsAppSkill()
    print(wa.add_contact("mum", "+919876543210"))
    print(wa.send_whatsapp("mum", "Hey, I'll be home late tonight."))
