import os
import base64
import cv2
import pyautogui
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(override=True)

class VisionSkill:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self._tmp_screen = "temp_screenshot.png"
        self._tmp_camera = "temp_webcam.jpg"
        print("[VISION] Vision module initialized.")

    def capture_screen(self) -> str:
        """Takes a screenshot, saves to temp file, returns path."""
        screenshot = pyautogui.screenshot()
        screenshot.save(self._tmp_screen)
        return self._tmp_screen

    def capture_camera(self):
        """Captures one webcam frame, saves to temp file, returns path or None."""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        cv2.imwrite(self._tmp_camera, frame)
        return self._tmp_camera

    def image_to_base64(self, image_path: str) -> str:
        """Converts an image file to a base64-encoded string."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _analyze_image(self, image_path: str, prompt: str) -> str:
        """Sends image + prompt to Gemini Vision. Returns JARVIS response."""
        try:
            image = Image.open(image_path)
            system_instruction = (
                "You are JARVIS, a highly intelligent AI assistant. "
                "Respond naturally and conversationally. Address the user as 'sir'. "
                "Be concise and informative, not robotic."
            )
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_image(image),
                            types.Part.from_text(text=prompt),
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
            return "I'm sorry sir, I encountered an error while analyzing the image."

    def _cleanup(self, path):
        if path and os.path.exists(path):
            os.remove(path)

    def describe_screen(self) -> str:
        """Screenshot → Gemini Vision → natural JARVIS description of the screen."""
        print("[VISION] Capturing and describing screen...")
        path = self.capture_screen()
        result = self._analyze_image(
            path,
            "Describe what you see on this screen naturally as JARVIS would. "
            "Be specific about apps, content, and information visible."
        )
        self._cleanup(path)
        return result

    def describe_camera(self, query: str = "What do you see?") -> str:
        """Webcam capture → Gemini Vision → conversational JARVIS response."""
        print("[VISION] Capturing camera feed...")
        path = self.capture_camera()
        if not path:
            return "I am unable to access the camera, sir."
        result = self._analyze_image(
            path,
            f"The user asked: {query}. Look at this camera image and respond as JARVIS — "
            "identify what you see, provide interesting information, be warm and conversational, not robotic."
        )
        self._cleanup(path)
        return result

    def identify_object(self, query: str = "What am I holding?") -> str:
        """Full object identification with facts and natural JARVIS delivery."""
        print("[VISION] Identifying object via camera...")
        path = self.capture_camera()
        if not path:
            return "I am unable to access the camera, sir."
        result = self._analyze_image(
            path,
            f"The user asked: '{query}'. Identify the object in this image. "
            "Respond as JARVIS: name the object, give 2-3 interesting facts, offer a relevant follow-up. "
            "Example style: 'That appears to be a Rubik's Cube sir, invented by Erno Rubik in 1974. "
            "There are over 43 quintillion possible configurations. Shall I look up solving algorithms?'"
        )
        self._cleanup(path)
        return result

    def read_text_from_image(self, source: str = "camera") -> str:
        """OCR via Gemini Vision — reads all visible text from camera or screen."""
        print(f"[VISION] Reading text from {source}...")
        path = self.capture_screen() if source == "screen" else self.capture_camera()
        if not path:
            return "I am unable to capture an image, sir."
        result = self._analyze_image(
            path,
            "Please read and transcribe all visible text in this image exactly as it appears. "
            "If there is no readable text, say so clearly."
        )
        self._cleanup(path)
        return result

    # Backward-compatible aliases
    def see_webcam(self, user_prompt: str = "What do you see?") -> str:
        return self.describe_camera(user_prompt)

    def see_screen(self, user_prompt: str = "What is on my screen?") -> str:  # noqa: ARG002
        return self.describe_screen()


if __name__ == "__main__":
    vision = VisionSkill()
    print(vision.describe_screen())
