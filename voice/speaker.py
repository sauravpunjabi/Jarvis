# This is JARVIS's "mouth" — it converts text into speech
# It tries to use your cloned JARVIS voice first (XTTS-v2)
# If that fails, it falls back to Microsoft's British Edge TTS voice

import os
import pygame
import tempfile
from dotenv import load_dotenv

# Load the path to our JARVIS voice WAV clip from .env
load_dotenv()

# Path to your JARVIS voice reference clip used for cloning
VOICE_CLIP = os.getenv("VOICE_CLIP_PATH", "assets/sounds/jarvis_voice.wav")

class JarvisSpeaker:
    def __init__(self):
        # Initialize pygame's audio mixer for playing sound files
        pygame.mixer.init()
        
        # Track whether XTTS-v2 voice cloning loaded successfully
        self.use_xtts = False
        self.tts = None
        
        # Try to load the voice cloning model
        self._load_tts()

    def _load_tts(self):
        # Try loading XTTS-v2 — the AI voice cloning model
        # This requires PyTorch which we're installing separately
        try:
            from TTS.api import TTS
            print("[SPEAKER] Loading XTTS-v2 voice cloning model...")
            print("[SPEAKER] First load takes 1-2 minutes, please wait...")
            
            # Load the XTTS-v2 model (downloads ~1.8GB on first run)
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
            
            # Make sure the voice reference clip exists
            if not os.path.exists(VOICE_CLIP):
                raise FileNotFoundError(f"Voice clip not found at: {VOICE_CLIP}")
            
            self.voice_clip = VOICE_CLIP
            self.use_xtts = True
            print("[SPEAKER] XTTS-v2 loaded. JARVIS voice clone ready.")
            
        except Exception as e:
            # If XTTS-v2 fails for any reason, use Edge TTS as backup
            print(f"[SPEAKER] XTTS-v2 unavailable ({e}), falling back to Edge TTS.")
            self.use_xtts = False

    def speak(self, text: str):
        # Print what JARVIS is saying so we can see it in the terminal too
        print(f"[JARVIS]: {text}")
        
        # Use cloned voice if available, otherwise use Edge TTS
        if self.use_xtts:
            self._speak_xtts(text)
        else:
            self._speak_edge(text)

    def _speak_xtts(self, text: str):
        # Generate speech using your cloned JARVIS voice
        try:
            # Create a temporary file to save the generated audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                tmp_path = f.name
            
            # Generate the audio using your voice clip as reference
            self.tts.tts_to_file(
                text=text,
                speaker_wav=self.voice_clip,  # Your JARVIS WAV clip
                language="en",
                file_path=tmp_path
            )
            
            # Play the generated audio then clean up the temp file
            self._play_audio(tmp_path)
            os.unlink(tmp_path)
            
        except Exception as e:
            # If cloned voice fails, fall back to Edge TTS
            print(f"[SPEAKER] XTTS error: {e}, falling back to Edge TTS.")
            self._speak_edge(text)

    def _speak_edge(self, text: str):
        # Use Microsoft Edge TTS — British male voice, sounds close to JARVIS
        import asyncio
        import edge_tts
        
        async def _run():
            # Create a temp file for the audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp_path = f.name
            
            # Generate speech with Ryan (British male) voice
            communicate = edge_tts.Communicate(text, voice="en-GB-RyanNeural")
            await communicate.save(tmp_path)
            return tmp_path
        
        # Run the async function and get the audio file path
        tmp_path = asyncio.run(_run())
        
        # Play audio AFTER the async function finishes
        # (important: file must be fully written before playing)
        self._play_audio(tmp_path)
        
        # Delete temp file after pygame is done with it
        # Delete temp file after pygame is done with it
        os.unlink(tmp_path)

    def _play_audio(self, file_path: str):
        # Load and play the audio file using pygame
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        
        # Wait until the audio finishes playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    def cleanup(self):
        """Release pygame resources cleanly."""
        pygame.mixer.quit()
        print("[SPEAKER] Audio resources cleaned up.")


# ── Standalone Test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    speaker = JarvisSpeaker()
    speaker.speak("Good evening, sir. JARVIS is online and ready.")
    speaker.cleanup()