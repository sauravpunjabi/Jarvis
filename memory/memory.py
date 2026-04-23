#this gives jarvis long term memory access sessions, facts are saved in a json file
#jarvis loads up the files and can use them in convo and update as it goes on.

import json
import os
from datetime import datetime

#config
MEMORY_FILE = "memory/jarvis_memory.json" 

DEFAULT_MEMORY = {
    "user": {
        "name": None,
        "city": None,
        "preferences": [],
        "notes": []
    },
    "jarvis": {
        "created_at": str(datetime.now().date()),
        "total_sessions": 0,
        "last_seen": None
    }
}


#main class file
class JarvisMemory:
    def __init__(self):
       print(f"[MEMORY] Loading memory system...")
       self.memory = self.load()
       self._update_session()
       print(f"[MEMORY] Memory loaded, Jarvis ready.  Total sessions: {self.memory['jarvis']['total_sessions']}")

    def load(self):
        """Load memory from JSON file. If file doesnt exist, create default."""
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r") as f:
                    data = json.load(f)
                print(f"[MEMORY] Loaded existing memory from {MEMORY_FILE}")
                return data
            except Exception as e:
                print(f"[MEMORY] Error loading memory: {e}, will restart.")
                return dict(DEFAULT_MEMORY)
        
        else:
            print(f"[MEMORY] No memory file found. Creating a new one at {MEMORY_FILE}")
            return dict(DEFAULT_MEMORY)
    
    def _save(self):
        """Save current memory to json file"""
        try:
            os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok = True)
            with open(MEMORY_FILE, "w") as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"[MEMORY] Error saving memory: {e}")

    def _update_session(self):
        """Increments session count and updates last seen timestamp"""
        self.memory["jarvis"]["total_sessions"] += 1
        self.memory["jarvis"]["last_seen"] = str(datetime.now())
        self._save()

#getters
    def get_user_name(self):
        """Return user's name or none, if not set"""
        return self.memory["user"]["name"]
    
    def get_user_city(self):
        """Return user's city or none, if not set"""
        return self.memory["user"]["city"]
    
    def get_user_preferences(self):
        """Return list of user's preferences or empty list"""
        return self.memory["user"]["preferances"]
    def get_user_notes(self):
        """Return list of user's notes or empty list"""
        return self.memory["user"]["notes"]
    def get_user_summary(self):
        """returns everything Jarvis knows by creating a prompt for Gemini."""
        name = self.memory["user"]["name"] or "unknown"
        city = self.memory["user"]["city"] or "unknown"
        prefs = self.memory["user"]["preferences"]
        notes = self.memory["user"]["notes"]
        sessions = self.memory["jarvis"]["total_sessions"]
        last = self.memory["jarvis"]["last_seen"]

        summary = f"User's name: {name}. City: {city}. Sessions so far: {sessions}"

        if prefs:
            summary += f"\nPreferences: {', '.join(prefs)}"
        if notes:
            summary += f"\nNotes: {', '.join(notes)}"
        if last:
            summary += f"\nLast seen: {last}"
        
        return summary

#setters
    def set_user_name(self,name:str):
        """Sets the user's name"""
        self.memory["user"]["name"] = name
        self._save()
        print(f"[MEMORY] Set user name to: {name}")

    def set_user_city(self, city: str):
        """Sets the user's city"""
        self.memory["user"]["city"] = city
        self._save()
        print(f"[MEMORY] Set user city to: {city}")
    
    def add_preference(self, preference: str):
        """Add a preference if not already present"""
        pref = preference.strip().lower()
        if pref not in self.memory["user"]["preferences"]:
            self.memory["user"]["preferences"].append(pref)
            self._save()
            print(f"[MEMORY] Added preference: {pref}")
    
    def add_note(self, note: str):
        """Add a note if not already present"""
        n = note.strip()
        if n not in self.memory["user"]["notes"]:
            self.memory["user"]["notes"].append(n)
            self._save()
            print(f"[MEMORY] Added note: {n}")
    
    def update_last_seen(self, text: str):
        """extracts and saves facts from natural language, is ran by main.py"""

        text_lower = text.lower()

        #detect name
        for phrase in ["my name is", "call me", "i am"]:
            if phrase in text_lower:
                name = text_lower.split(phrase)[-1].strip().split()[0].capitalize()
                self.set_user_name(name)
                return f"name: {name}"
        
        #detect city
        for phrase in ["i live in", "i'm from", "based in"]:
            if phrase in text_lower:
                city = text_lower.split(phrase)[-1].strip().split()[0].capitalize()
                self.set_user_city(city)
                return f"city: {city}"

        #detect preferences/hobbies
        for phrase in ["i prefer ", "i like ", "i love ", "i enjoy "]:
            if phrase in text_lower:
                pref = text_lower.split(phrase)[-1].strip()
                self.add_preference(pref)
                return f"preference:{pref}"
        return None #if no input

        #reset
    def wipe(self):
        """Reset all memory to default. Use carefully."""
        self.memory = dict(DEFAULT_MEMORY)
        self._save()
        print("[MEMORY] Memory wiped and reset to default.")

#standalone test

if __name__ == "__main__":
    mem = JarvisMemory()

    print("\n--- Setting user info ---")
    mem.set_user_name("Saurav")
    mem.set_user_city("Dhule")
    mem.add_preference("dark theme")
    mem.add_note("has a Dell G15 laptop with RTX 3050")
    mem.add_note("likes Iron Man")

    print("\n--- Memory Summary ---")
    print(mem.get_user_summary())

    print("\n--- Testing update_last_seen ---")
    mem.update_last_seen("I prefer no music after midnight")
    mem.update_last_seen("my name is Tony")

    print("\n--- Final Summary ---")
    print(mem.get_user_summary())