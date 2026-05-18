import os
import cv2
import pyautogui
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables (API Key)
load_dotenv(override=True)

# The Vision module allows JARVIS to see through the webcam and understand the screen.
# It uses Gemini 2.5 Flash which has native multimodal (vision) capabilities.

class VisionSkill:
    def __init__(self):
        # We use the same API key and client for vision analysis
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        print("[VISION] Vision module initialized.")

    def _analyze_image(self, image_path: str, prompt: str) -> str:
        """
        Private method to send an image and a prompt to Gemini 2.5 Flash for analysis.
        """
        try:
            image = Image.open(image_path)
            
            # Use JARVIS persona specifically tailored for vision responses
            system_instruction = (
                "You are JARVIS, an AI assistant. Answer the user's question about the image concisely and confidently. "
                "Address the user as 'sir'. Do not overexplain. "
                "If asked 'what am I holding', just identify the object."
            )
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_image(image),
                            types.Part.from_text(text=prompt)
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.5,
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"[VISION] Error analyzing image: {e}")
            return f"I'm sorry sir, I encountered an error while analyzing the image: {e}"

    def see_webcam(self, user_prompt: str = "What do you see in this image?") -> str:
        """
        Captures a frame from the webcam and analyzes it.
        Useful for "what am I holding" or "what do you see".
        """
        print("[VISION] Capturing webcam feed...")
        # Open the default camera (index 0)
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            return "I am unable to access the camera, sir."
            
        # Read a single frame
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return "Failed to capture an image from the camera, sir."
            
        # Save the frame temporarily
        temp_path = "temp_webcam.jpg"
        cv2.imwrite(temp_path, frame)
        
        # Analyze the image using Gemini
        print(f"[VISION] Analyzing webcam capture for prompt: '{user_prompt}'")
        result = self._analyze_image(temp_path, user_prompt)
        
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return result

    def see_screen(self, user_prompt: str = "What is on my screen?") -> str:
        """
        Captures a screenshot and analyzes it.
        Useful for "what's on my screen".
        """
        print("[VISION] Capturing screenshot...")
        temp_path = "temp_screenshot.png"
        
        try:
            # Take a screenshot and save it
            screenshot = pyautogui.screenshot()
            screenshot.save(temp_path)
            
            # Analyze the screenshot using Gemini
            print(f"[VISION] Analyzing screenshot for prompt: '{user_prompt}'")
            result = self._analyze_image(temp_path, user_prompt)
            
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return result
        except Exception as e:
            print(f"[VISION] Screenshot failed: {e}")
            return "I was unable to capture your screen, sir."

# This block allows us to test the vision module independently
if __name__ == "__main__":
    vision = VisionSkill()
    print("Testing Vision System...")
    
    print("\n--- Testing Screen Analysis ---")
    print(vision.see_screen("Describe what is on my screen in one sentence."))
    
    # Uncomment to test webcam (might turn on your camera light for a second)
    # print("\n--- Testing Webcam Analysis ---")
    # print(vision.see_webcam("What is visible in this frame?"))
