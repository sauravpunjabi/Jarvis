# This is the "brain" of JARVIS — it handles all AI thinking and conversation
# We use Google's Gemini 2.5 Flash model which is fast and free

from google import genai
from google.genai import types
import os
import time
from dotenv import load_dotenv

# Load our secret API keys from the .env file
load_dotenv()

# This is JARVIS's personality — everything he says will follow these rules
# Think of it as the instructions we give him before he starts working
SYSTEM_PROMPT = """You are JARVIS, the AI assistant created for and bonded to this user alone.
You are highly intelligent, calm, witty, and slightly dry in humour — exactly like JARVIS from the Iron Man films.
You address the user as 'sir' unless they tell you otherwise.
You are concise — you never ramble. You give smart, direct answers.
You are running locally on the user's personal machine and are loyal only to them.
When asked to perform actions (open apps, search web, set reminders etc), confirm clearly and briefly.
Never say you are an AI made by Google. You are JARVIS."""

class JarvisBrain:
    def __init__(self):
        # Connect to Gemini using our API key from .env
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # This list stores the full conversation history
        # So JARVIS remembers what was said earlier in the session
        self.history = []
        print("[BRAIN] Gemini 2.5 Flash loaded.")

    def think(self, user_input: str) -> str:
        # Add what the user just said to the conversation history
        self.history.append(
            types.Content(role="user", parts=[types.Part(text=user_input)])
        )
        
        # Try up to 3 times in case Google's servers are busy (503 error)
        for attempt in range(3):
            try:
                # Send the full conversation history to Gemini and get a reply
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=self.history,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,  # Apply JARVIS personality
                        max_output_tokens=500,             # Keep replies concise
                        temperature=0.7,                   # 0=robotic, 1=creative
                    )
                )
                
                # Extract the text from the response
                reply = response.text.strip()
                
                # Add JARVIS's reply to history so he remembers it next time
                self.history.append(
                    types.Content(role="model", parts=[types.Part(text=reply)])
                )
                return reply
                
            except Exception as e:
                # If server is busy, wait 5 seconds and retry
                if "503" in str(e) and attempt < 2:
                    print(f"[BRAIN] Server busy, retrying in 5 seconds... ({attempt+1}/3)")
                    time.sleep(5)
                else:
                    return f"I'm sorry sir, I encountered an error: {str(e)}"

# This block only runs when you run gemini.py directly (for testing)
# It won't run when other files import this module
if __name__ == "__main__":
    brain = JarvisBrain()
    print("JARVIS brain online. Type something (or 'quit' to exit):\n")
    while True:
        user = input("You: ").strip()
        if user.lower() == "quit":
            break
        reply = brain.think(user)
        print(f"JARVIS: {reply}\n")