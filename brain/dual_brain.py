# This module manages JARVIS's two brains — Ollama (local) and Gemini (cloud)
# Default brain is Ollama so JARVIS works offline without any API calls
# If Ollama goes offline mid-session, it automatically falls back to Gemini

# Try absolute imports first (when called from project root via main.py)
# Fall back to relative imports when this file is run directly for testing
try:
    from brain.ollama_brain import JarvisOllamaBrain
    from brain.gemini import JarvisBrain as JarvisGeminiBrain
except ImportError:
    from ollama_brain import JarvisOllamaBrain
    from gemini import JarvisBrain as JarvisGeminiBrain

# Labels used for logging and announcements
BRAIN_OLLAMA = "ollama"
BRAIN_GEMINI = "gemini"


class JarvisDualBrain:
    def __init__(self):
        # Initialise both brains — Gemini needs API key from .env, Ollama needs server running
        print("[DUAL_BRAIN] Loading both brains...")
        self.ollama = JarvisOllamaBrain()
        self.gemini = JarvisGeminiBrain()

        # Start with Ollama as the default (local, private, no API cost)
        self._active = BRAIN_OLLAMA
        print(f"[DUAL_BRAIN] Active brain: {self._active.upper()}")

    def get_active_brain(self) -> str:
        # Returns which brain is currently active: 'ollama' or 'gemini'
        return self._active

    def switch_to_ollama(self) -> str:
        # Switch to the local Ollama brain — works offline, no API key needed
        self._active = BRAIN_OLLAMA
        print("[DUAL_BRAIN] Switched to Ollama (local mode).")
        return "Switching to local mode, sir. I am now running entirely on your machine."

    def switch_to_gemini(self) -> str:
        # Switch to the cloud Gemini brain — requires internet and API key
        self._active = BRAIN_GEMINI
        print("[DUAL_BRAIN] Switched to Gemini (cloud mode).")
        return "Switching to Gemini, sir. Cloud intelligence is now active."

    def reset(self):
        # Clear conversation history on both brains simultaneously
        self.ollama.reset()
        self.gemini.history = []
        print("[DUAL_BRAIN] Both brains reset.")

    def chat(self, user_input: str) -> str:
        # Route the message to whichever brain is currently active
        # If Ollama is selected but has gone offline, auto-fall back to Gemini

        if self._active == BRAIN_OLLAMA:
            # Check if Ollama is still reachable before sending the message
            if not self.ollama.is_available():
                print("[DUAL_BRAIN] Ollama offline — falling back to Gemini automatically.")
                self._active = BRAIN_GEMINI
                # Inform the user that the fallback happened transparently
                fallback_notice = (
                    "Sir, the local Ollama server appears to be offline. "
                    "I have automatically switched to Gemini. "
                )
                gemini_reply = self.gemini.think(user_input)
                return fallback_notice + gemini_reply

            # Ollama is online — send the message to it
            return self.ollama.chat(user_input)

        # Gemini is the active brain — send directly
        return self.gemini.think(user_input)


# This block only runs when you execute dual_brain.py directly (for testing)
# It will not run when other modules import this file
if __name__ == "__main__":
    print("[DUAL_BRAIN] Starting dual brain test...\n")
    brain = JarvisDualBrain()

    print(f"\n--- Active brain: {brain.get_active_brain().upper()} ---")

    # Test 1: Chat using the default Ollama brain
    print("\n[TEST 1] Sending message via Ollama brain...")
    reply = brain.chat("Hello JARVIS, which brain are you running on right now?")
    print(f"JARVIS: {reply}\n")

    # Test 2: Switch to Gemini and chat
    print("[TEST 2] Switching to Gemini...")
    print(brain.switch_to_gemini())
    reply = brain.chat("And now which brain are you using, JARVIS?")
    print(f"JARVIS: {reply}\n")

    # Test 3: Switch back to Ollama
    print("[TEST 3] Switching back to Ollama...")
    print(brain.switch_to_ollama())
    print(f"Active brain is now: {brain.get_active_brain().upper()}")

    # Test 4: Reset both brains
    print("\n[TEST 4] Resetting both brains...")
    brain.reset()
    print("[DUAL_BRAIN] All tests complete.")
