import os
import json
import cv2

MEMORY_FILE = "memory/jarvis_memory.json"
FACES_DIR = "data/known_faces"

class FaceRecognitionSkill:
    def __init__(self):
        os.makedirs(FACES_DIR, exist_ok=True)
        self._fr_available = self._check_face_recognition()
        print(f"[FACE] Face recognition module initialized. "
              f"(face_recognition lib: {'available' if self._fr_available else 'not installed — using OpenCV fallback'})")

    def _check_face_recognition(self) -> bool:
        try:
            import face_recognition  # noqa: F401
            return True
        except ImportError:
            return False

    def _load_known_faces(self):
        """Loads known face encodings from the faces directory."""
        import face_recognition
        known_encodings = []
        known_names = []
        for filename in os.listdir(FACES_DIR):
            if filename.endswith((".jpg", ".png")):
                name = os.path.splitext(filename)[0]
                path = os.path.join(FACES_DIR, filename)
                image = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    known_encodings.append(encodings[0])
                    known_names.append(name)
        return known_encodings, known_names

    def register_face(self, name: str) -> str:
        """Captures a webcam frame and saves it as the reference face for name."""
        print(f"[FACE] Registering face for: {name}")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return "I am unable to access the camera, sir."
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return "Failed to capture image from camera, sir."

        save_path = os.path.join(FACES_DIR, f"{name.lower()}.jpg")
        cv2.imwrite(save_path, frame)

        # Also record in memory
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r") as f:
                    data = json.load(f)
                data.setdefault("known_faces", [])
                if name.lower() not in data["known_faces"]:
                    data["known_faces"].append(name.lower())
                with open(MEMORY_FILE, "w") as f:
                    json.dump(data, f, indent=2)
            except Exception:
                pass

        return f"Face registered for {name}, sir. I'll recognize you next time."

    def recognize_face(self) -> str:
        """Captures webcam frame and matches against known faces."""
        print("[FACE] Attempting face recognition...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return "I am unable to access the camera, sir."
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return "Failed to capture image from camera, sir."

        if self._fr_available:
            return self._recognize_with_lib(frame)
        else:
            return self._recognize_with_opencv(frame)

    def _recognize_with_lib(self, frame) -> str:
        """Uses face_recognition library for accurate matching."""
        import face_recognition
        import numpy as np

        known_encodings, known_names = self._load_known_faces()
        if not known_encodings:
            return "I have no registered faces to compare against, sir."

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if not face_encodings:
            return "I don't see any faces in frame, sir."

        for encoding in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.5)
            if True in matches:
                name = known_names[matches.index(True)].capitalize()
                return f"Good to see you, {name}, sir."

        return "I don't recognize this person, sir."

    def _recognize_with_opencv(self, frame) -> str:
        """Fallback: detects faces using OpenCV Haar cascade (no identification)."""
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        if len(faces) == 0:
            return "I don't see any faces in frame, sir."
        return (
            f"I can see {len(faces)} face(s) in frame, sir. "
            "Install the face-recognition library for identity matching: pip install face-recognition"
        )


if __name__ == "__main__":
    fr = FaceRecognitionSkill()
    print(fr.recognize_face())
