import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# The Skill Router determines exactly which module should handle a user's request.
# It uses Gemini 2.5 Flash at temperature 0 for strictly deterministic classification.

class SkillRouter:
    def __init__(self):
        # Initialize Gemini Client
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        # Valid categories according to the JARVIS architecture
        self.valid_categories = [
            "pc_control",
            "weather",
            "media",
            "files",
            "vision",
            "whatsapp",
            "email",
            "downloader",
            "browser",
            "web_search",
            "general"
        ]
        print("[BRAIN] Skill Router initialized.")

    def route_intent(self, user_input: str) -> str:
        """
        Takes the user's input and classifies it into exactly one of the valid categories.
        Returns ONLY the category string.
        """
        system_instruction = (
            "You are the routing brain of an AI OS assistant named JARVIS. "
            "Your ONLY job is to classify the user's input into exactly ONE of the following categories: "
            f"{', '.join(self.valid_categories)}. "
            "Return NOTHING ELSE. Only the exact string of the category."
        )
        
        import time
        for attempt in range(3):
            try:
                # We use temperature 0.0 because we want strict classification, not creativity
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[types.Content(role="user", parts=[types.Part.from_text(text=user_input)])],
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.0,
                    )
                )
                
                category = response.text.strip().lower()
                
                # Fallback to general if the model outputs something weird
                if category not in self.valid_categories:
                    print(f"[BRAIN] Warning: Unrecognised category '{category}', defaulting to 'general'")
                    return "general"
                    
                return category
                
            except Exception as e:
                if "503" in str(e) and attempt < 2:
                    print(f"[BRAIN] Router server busy, retrying in 3 seconds... ({attempt+1}/3)")
                    time.sleep(3)
                else:
                    print(f"[BRAIN] Error in routing intent: {e}")
                    return "general"

# This block allows us to test the router independently
if __name__ == "__main__":
    router = SkillRouter()
    print("Testing Skill Router...\n")
    
    # Test cases to verify routing accuracy
    test_queries = [
        "What's the weather like in New York?",
        "Play Hans Zimmer on Spotify",
        "Search Google for python tutorials",
        "What am I holding right now?",
        "Read this pdf file",
        "Turn down the volume",
        "Send a whatsapp to John",
        "Hello JARVIS, how are you today?"
    ]
    
    for query in test_queries:
        result = router.route_intent(query)
        print(f"Query: '{query}'")
        print(f"Routed to: [{result}]\n")
