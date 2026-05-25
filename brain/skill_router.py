import os
import json
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(override=True)

VALID_CATEGORIES = [
    "open_app", "open_website",
    "weather", "time", "date",
    "media_play", "media_download", "media_stop",
    "web_search", "news",
    "files_read", "files_create", "files_list",
    "vision_screen", "vision_camera",
    "whatsapp", "email",
    "reminder", "face_recognize",
    "screenshot", "battery", "volume_up", "volume_down", "mute",
    "lock", "shutdown", "restart", "system_stats",
    "conflict_events", "conflict_risk", "conflict_commodity", "conflict_country",
    "pc_control", "general",
]

_CLASSIFY_SYS = (
    "You are JARVIS's intent classifier. Return ONLY one exact label from this list — nothing else:\n"
    + ", ".join(VALID_CATEGORIES)
)

_EXTRACT_SYS = (
    "Extract key parameters from the user command and return them as a flat JSON object. "
    "Use these field names:\n"
    "  query, target, city, topic, path, filename, content, contact, message, to, subject, body, time, level, action, folder\n"
    "Return only the fields that are clearly present in the command. Return ONLY valid JSON."
)


class SkillRouter:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self._load_skills()
        print("[ROUTER] Skill Router initialized with full dispatch.")

    def _load_skills(self):
        from brain.gemini import JarvisBrain
        from skills.pc_control import PcController
        from skills.weather import WeatherSkill
        from skills.media import MediaSkill
        from skills.vision import VisionSkill
        from skills.files import FilesSkill
        from skills.whatsapp import WhatsAppSkill
        from skills.email_skill import EmailSkill
        from skills.news import NewsSkill
        from skills.web_search import WebSearcher

        self.brain    = JarvisBrain()
        self.pc       = PcController()
        self.weather  = WeatherSkill()
        self.media    = MediaSkill()
        self.vision   = VisionSkill()
        self.files    = FilesSkill()
        self.whatsapp = WhatsAppSkill()
        self.email    = EmailSkill()
        self.news     = NewsSkill()
        self.web      = WebSearcher()

        try:
            from skills.face_recognition_skill import FaceRecognitionSkill
            self.face = FaceRecognitionSkill()
        except Exception as e:
            print(f"[ROUTER] Face recognition unavailable: {e}")
            self.face = None

    # ── Gemini helpers ───────────────────────────────────────────────────────

    def _gemini(self, system: str, user: str, temperature: float = 0.0, json_mode: bool = False) -> str:
        kwargs = {"temperature": temperature}
        if json_mode:
            kwargs["response_mime_type"] = "application/json"
        for attempt in range(3):
            try:
                r = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[types.Content(role="user", parts=[types.Part.from_text(text=user)])],
                    config=types.GenerateContentConfig(system_instruction=system, **kwargs),
                )
                return r.text.strip()
            except Exception as e:
                if "503" in str(e) and attempt < 2:
                    time.sleep(3)
                else:
                    print(f"[ROUTER] Gemini error: {e}")
                    return ""
        return ""

    # ── Step 1: Classify ─────────────────────────────────────────────────────

    def _classify(self, command: str) -> str:
        result = self._gemini(_CLASSIFY_SYS, command, temperature=0.0).lower().strip()
        if result not in VALID_CATEGORIES:
            print(f"[ROUTER] Unknown category '{result}', defaulting to general")
            return "general"
        return result

    # ── Step 2: Extract params ───────────────────────────────────────────────

    def _extract(self, command: str, category: str) -> dict:
        prompt = f'Category: {category}\nCommand: "{command}"'
        raw = self._gemini(_EXTRACT_SYS, prompt, temperature=0.0, json_mode=True)
        try:
            return json.loads(raw) if raw else {}
        except Exception:
            return {}

    # ── Step 3: Dispatch ─────────────────────────────────────────────────────

    def _dispatch(self, category: str, p: dict, command: str) -> str:
        desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")

        if category == "open_app":
            return self.pc.open_anything(p.get("target") or p.get("query") or command)

        elif category == "open_website":
            return self.pc.open_anything(p.get("target") or p.get("url") or command)

        elif category == "weather":
            return self.weather.get_weather(p.get("city"))

        elif category == "time":
            return self.weather.get_time()

        elif category == "date":
            return self.weather.get_date()

        elif category == "media_play":
            return self.media.play_youtube_audio(p.get("query", command))

        elif category == "media_download":
            return self.media.download_youtube(p.get("query", command))

        elif category == "media_stop":
            return self.media.stop_media()

        elif category == "web_search":
            return self.web.smart_search(p.get("query", command))

        elif category == "news":
            return self.news.get_headlines(p.get("topic"))

        elif category == "files_read":
            path = p.get("path", "")
            return self.files.summarize_file(path) if path else "Which file shall I read, sir?"

        elif category == "files_create":
            fname = p.get("filename", "note.txt")
            return self.files.create_file(os.path.join(desktop, fname), p.get("content", ""))

        elif category == "files_list":
            return self.files.list_files(p.get("folder", desktop))

        elif category == "vision_screen":
            return self.vision.describe_screen()

        elif category == "vision_camera":
            return self.vision.describe_camera(p.get("query", command))

        elif category == "whatsapp":
            contact = p.get("contact", "")
            if not contact:
                return "Who should I message, sir?"
            return self.whatsapp.send_whatsapp(contact, p.get("message", ""))

        elif category == "email":
            to = p.get("to", "")
            if not to:
                return "Who should I email, sir?"
            return self.email.send_email(to, p.get("subject", ""), p.get("body", ""))

        elif category == "reminder":
            return self.weather.set_reminder(p.get("time", ""), p.get("message", command))

        elif category == "face_recognize":
            return self.face.recognize_face() if self.face else "Face recognition not available, sir."

        elif category == "screenshot":
            return self.pc.take_screenshot()

        elif category == "battery":
            return self.pc.get_battery()

        elif category == "volume_up":
            return self.pc.volume_up()

        elif category == "volume_down":
            return self.pc.volume_down()

        elif category == "mute":
            return self.pc.mute()

        elif category == "lock":
            return self.pc.lock_computer()

        elif category == "shutdown":
            return self.pc.shutdown()

        elif category == "restart":
            return self.pc.restart()

        elif category == "system_stats":
            return self.pc.get_system_stats()

        elif category in ("conflict_events", "conflict_risk", "conflict_commodity", "conflict_country"):
            return "ConflictScope integration coming soon, sir."

        elif category == "pc_control":
            cmd_l = command.lower()
            level = p.get("level")
            if "volume up" in cmd_l:       return self.pc.volume_up()
            if "volume down" in cmd_l:     return self.pc.volume_down()
            if "mute" in cmd_l:            return self.pc.mute()
            if "screenshot" in cmd_l:      return self.pc.take_screenshot()
            if "battery" in cmd_l:         return self.pc.get_battery()
            if "lock" in cmd_l:            return self.pc.lock_computer()
            if "shutdown" in cmd_l:        return self.pc.shutdown()
            if "restart" in cmd_l:         return self.pc.restart()
            if "stats" in cmd_l:           return self.pc.get_system_stats()
            if level is not None:          return self.media.set_volume(int(level))
            return self.pc.open_anything(p.get("target") or p.get("query") or command)

        else:
            return self.brain.think(command)

    # ── Public entry point ───────────────────────────────────────────────────

    def route(self, command: str) -> tuple:
        """Classify → extract params → dispatch. Returns (response, category)."""
        category = self._classify(command)
        print(f"[ROUTER] {category} ← '{command}'")
        params = self._extract(command, category)
        if params:
            print(f"[ROUTER] params: {params}")
        response = self._dispatch(category, params, command)
        return response, category

    def route_intent(self, user_input: str) -> str:
        """Backward-compatible: returns just the category string."""
        return self._classify(user_input)


if __name__ == "__main__":
    router = SkillRouter()
    tests = [
        "open YouTube",
        "what's the weather in London",
        "play Blinding Lights",
        "what time is it",
        "take a screenshot",
        "volume up",
        "what am I holding",
        "latest tech news",
        "remind me in 10 minutes to drink water",
    ]
    for cmd in tests:
        resp, skill = router.route(cmd)
        print(f"\n[{skill}] {resp}")
