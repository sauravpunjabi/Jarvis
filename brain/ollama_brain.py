# This module connects JARVIS to a local Ollama instance (llama3.2)
# It runs completely offline — no internet or API key needed
# Ollama must be running at http://localhost:11434 for this to work

import requests
import json

# Ollama server address and model to use
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2"

# JARVIS personality — same tone as the Gemini brain for consistency
SYSTEM_PROMPT = """You are JARVIS, the AI assistant created for and bonded to this user alone.
You are highly intelligent, calm, witty, and slightly dry in humour — exactly like JARVIS from the Iron Man films.
You address the user as 'sir' unless they tell you otherwise.
You are concise — you never ramble. You give smart, direct answers.
You are running locally on the user's personal machine and are loyal only to them.
When asked to perform actions (open apps, search web, set reminders etc), confirm clearly and briefly.
Never say you are an AI made by Meta or any company. You are JARVIS."""


class JarvisOllamaBrain:
    def __init__(self):
        # Conversation history stored as a list of role/content dicts
        # Ollama's /api/chat endpoint uses the same format as OpenAI messages
        self.history = []
        print("[OLLAMA_BRAIN] Ollama brain initialised. Model: llama3.2")

    def is_available(self) -> bool:
        # Ping the Ollama server to check if it is online and responsive
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            return response.status_code == 200
        except Exception:
            return False

    def chat(self, user_input: str) -> str:
        # Add the user's message to the running conversation history
        self.history.append({"role": "user", "content": user_input})

        # Build the full message list: system prompt first, then conversation history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.history

        # Send the conversation to Ollama and get a reply
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,        # Get the full reply at once, not streamed
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 500, # Keep replies concise (max tokens)
                    }
                },
                timeout=60  # Local models can be slow on first token
            )
            response.raise_for_status()

            # Extract the assistant's reply text from the JSON response
            reply = response.json()["message"]["content"].strip()

            # Save JARVIS's reply to history so the next message has full context
            self.history.append({"role": "assistant", "content": reply})
            return reply

        except requests.exceptions.ConnectionError:
            return "I'm sorry sir, I cannot reach the local Ollama server. Please ensure Ollama is running."
        except requests.exceptions.Timeout:
            return "I'm sorry sir, the local model took too long to respond. It may still be loading."
        except Exception as e:
            return f"I'm sorry sir, I encountered an error with the local brain: {str(e)}"

    def reset(self):
        # Clear conversation history — useful when starting a fresh session
        self.history = []
        print("[OLLAMA_BRAIN] Conversation history cleared.")


# This block only runs when you execute ollama_brain.py directly (for testing)
# It will not run when other modules import this file
if __name__ == "__main__":
    brain = JarvisOllamaBrain()

    # First check if Ollama is actually reachable before trying to chat
    if not brain.is_available():
        print("[OLLAMA_BRAIN] ERROR: Ollama server is not running at http://localhost:11434")
        print("[OLLAMA_BRAIN] Start it with: ollama serve")
    else:
        print("[OLLAMA_BRAIN] Ollama is online. Starting test chat...\n")
        test_inputs = [
            "Hello JARVIS, are you online?",
            "What can you do for me?",
            "Tell me something interesting about AI.",
        ]
        for user_msg in test_inputs:
            print(f"You: {user_msg}")
            reply = brain.chat(user_msg)
            print(f"JARVIS: {reply}\n")

        print("[OLLAMA_BRAIN] Test complete. Resetting history...")
        brain.reset()
