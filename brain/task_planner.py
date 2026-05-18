import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# The Task Planner breaks down complex requests into actionable, sequential steps.
# It acts as the autonomous reasoning engine of JARVIS.

class TaskPlanner:
    def __init__(self):
        # Initialize Gemini Client
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        print("[BRAIN] Task Planner initialized.")

    def plan_task(self, user_request: str) -> list:
        """
        Takes a complex user request and breaks it into sequential actionable steps.
        Returns a list of strings where each string is a step.
        """
        system_instruction = (
            "You are JARVIS's internal Task Planner. "
            "Your job is to break down complex user requests into simple, sequential, autonomous steps. "
            "Think logically. If an action is dangerous (installing software, deleting files), "
            "you MUST include a 'Ask confirmation' step before proceeding. "
            "Output your response strictly as a JSON array of strings, where each string is a step. "
            "Example input: 'Download VLC player' "
            "Example output: [\"Open browser\", \"Search official VLC site\", \"Download installer\", \"Ask confirmation\", \"Run installer\"] "
            "Do not output markdown, just the JSON array."
        )
        
        import time
        for attempt in range(3):
            try:
                print(f"[BRAIN] Planning task: '{user_request}'")
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[types.Content(role="user", parts=[types.Part.from_text(text=user_request)])],
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2, # Low temperature for logical consistency
                        response_mime_type="application/json"
                    )
                )
                
                # Parse the JSON response
                steps = json.loads(response.text.strip())
                return steps
                
            except Exception as e:
                if "503" in str(e) and attempt < 2:
                    print(f"[BRAIN] Planner server busy, retrying in 3 seconds... ({attempt+1}/3)")
                    time.sleep(3)
                else:
                    print(f"[BRAIN] Error planning task: {e}")
                    # Fallback to a single step
                    return [user_request]
                    
        return [user_request]

# This block allows us to test the planner independently
if __name__ == "__main__":
    planner = TaskPlanner()
    print("Testing Task Planner...\n")
    
    # Test cases for autonomous reasoning
    test_queries = [
        "Install VLC player",
        "Delete all files in the downloads folder",
        "Send an email to boss saying I will be late"
    ]
    
    for query in test_queries:
        print(f"\nRequest: {query}")
        plan = planner.plan_task(query)
        print("Plan:")
        for i, step in enumerate(plan, 1):
            print(f"  {i}. {step}")
