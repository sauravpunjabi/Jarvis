import sys
import argparse
import threading
import time
import random
from datetime import datetime
from dotenv import load_dotenv

_READY_LINES = [
    "How can I help?",
    "At your service.",
    "Go ahead, sir.",
    "Listening.",
    "What do you need?",
    "Ready when you are.",
    "Online and awaiting, sir.",
    "Speak your command."
]

JARVIS_LOGO = """
   ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
   ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
   ██║███████║██████╔╝██║   ██║██║███████╗
██ ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
 ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
  Just A Rather Very Intelligent System
"""


def _greeting(name: str) -> str:
    h = datetime.now().hour
    period = "morning" if h < 12 else "afternoon" if h < 18 else "evening"
    suffix = f", {name}" if name else ""
    return f"Good {period}{suffix}. All systems online, sir."


def _voice_loop(router, speaker, listener, memory, dual_brain, hud=None):
    """
    Main voice loop — runs in a background thread when HUD is active,
    or directly in the main thread when --no-hud is used.
    """
    while True:
        try:
            if hud:
                hud.set_status("LISTENING")

            listener.wait_for_wake_word()
            speaker.speak(random.choice(_READY_LINES))
            time.sleep(0.3)  # let speaker audio settle before opening mic

            audio   = listener.record_command()
            command = listener.transcribe(audio)

            if not command or len(command.strip()) < 3:
                speaker.speak("I didn't catch that, sir.")
                continue

            print(f"\n[YOU] {command}")

            if hud:
                hud.set_status("THINKING")

            # Intercept brain-switching voice commands before routing to skills
            lower_cmd = command.lower()
            switched = None
            if any(p in lower_cmd for p in ["switch to gemini", "gemini mode", "cloud mode", "use gemini"]):
                switched = dual_brain.switch_to_gemini()
            elif any(p in lower_cmd for p in ["switch to local", "local mode", "offline mode", "use ollama", "switch to ollama"]):
                switched = dual_brain.switch_to_ollama()

            if switched:
                print(f"[JARVIS] (brain_switch) {switched}")
                if hud:
                    hud.set_transcript(command, switched)
                    hud.set_status("SPEAKING")
                speaker.speak(switched)
                continue

            response, skill = router.route(command)
            memory.update_last_seen(command)

            print(f"[JARVIS] ({skill}) {response}")

            if hud:
                hud.set_transcript(command, response)
                hud.set_status("SPEAKING")
                # Refresh memory panel after each interaction
                hud.update_memory(
                    memory.get_user_name(),
                    memory.get_user_city(),
                    memory.memory["jarvis"]["total_sessions"],
                )

            speaker.speak(response)

        except Exception as e:
            print(f"[JARVIS] Voice loop error: {e}")


def _text_loop(router, memory, dual_brain):
    """Fallback text-based loop — useful for testing without a mic."""
    print("\n[JARVIS] Text mode. Type a command or 'quit' to exit.\n")
    while True:
        try:
            command = input("You: ").strip()
            if command.lower() in ("quit", "exit", "stop"):
                print("JARVIS: Goodbye, sir.")
                break
            if not command:
                continue

            # Intercept brain-switching commands before routing to skills
            lower_cmd = command.lower()
            if any(p in lower_cmd for p in ["switch to gemini", "gemini mode", "cloud mode", "use gemini"]):
                r = dual_brain.switch_to_gemini()
                print(f"JARVIS [brain_switch]: {r}\n")
                continue
            elif any(p in lower_cmd for p in ["switch to local", "local mode", "offline mode", "use ollama", "switch to ollama"]):
                r = dual_brain.switch_to_ollama()
                print(f"JARVIS [brain_switch]: {r}\n")
                continue

            response, skill = router.route(command)
            memory.update_last_seen(command)
            print(f"JARVIS [{skill}]: {response}\n")
        except KeyboardInterrupt:
            print("\nJARVIS: Goodbye, sir.")
            break


def main():
    load_dotenv(override=True)

    parser = argparse.ArgumentParser(description="JARVIS AI Assistant")
    parser.add_argument("--no-hud",  action="store_true", help="Run without the HUD overlay")
    parser.add_argument("--text",    action="store_true", help="Text mode — no microphone needed")
    args = parser.parse_args()

    print(JARVIS_LOGO)

    # ── Core modules (always loaded) ─────────────────────────────────────────
    from memory.memory import JarvisMemory
    from brain.skill_router import SkillRouter
    from brain.dual_brain import JarvisDualBrain
    from voice.speaker import JarvisSpeaker

    memory     = JarvisMemory()
    router     = SkillRouter()
    dual_brain = JarvisDualBrain()
    speaker    = JarvisSpeaker()

    # Greet
    name     = memory.get_user_name()
    greeting = _greeting(name)
    print(f"[JARVIS] {greeting}")
    speaker.speak(greeting)

    # Announce which brain is active on startup
    brain_label = "local Ollama" if dual_brain.get_active_brain() == "ollama" else "Gemini"
    brain_msg   = f"Active brain is {brain_label}, sir."
    print(f"[JARVIS] {brain_msg}")
    speaker.speak(brain_msg)

    # ── Text mode ────────────────────────────────────────────────────────────
    if args.text:
        _text_loop(router, memory, dual_brain)
        speaker.cleanup()
        sys.exit(0)

    # ── Voice modules ────────────────────────────────────────────────────────
    from voice.listener import JarvisListener
    listener = JarvisListener()

    def _shutdown():
        speaker.speak("Goodbye sir. Shutting down.")
        listener.cleanup()
        speaker.cleanup()
        sys.exit(0)

    # ── No-HUD: run voice loop in main thread ─────────────────────────────────
    if args.no_hud:
        try:
            _voice_loop(router, speaker, listener, memory, dual_brain, hud=None)
        except KeyboardInterrupt:
            _shutdown()
        return

    # ── HUD mode: Qt in main thread, voice loop in background thread ──────────
    from PyQt6.QtWidgets import QApplication
    from hud.hud import JarvisHUD

    app    = QApplication(sys.argv)
    screen = app.primaryScreen().geometry()

    hud = JarvisHUD()
    hud.setGeometry(0, 0, screen.width(), screen.height())
    hud.update_memory(name or "Unknown", memory.get_user_city() or "Unknown",
                      memory.memory["jarvis"]["total_sessions"])
    hud.set_status("LISTENING")
    hud.show()

    # Start voice loop in daemon thread
    t = threading.Thread(
        target=_voice_loop,
        args=(router, speaker, listener, memory, dual_brain, hud),
        daemon=True,
    )
    t.start()

    try:
        exit_code = app.exec()
    except KeyboardInterrupt:
        exit_code = 0
    finally:
        _shutdown()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
