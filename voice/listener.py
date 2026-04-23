# voice/listener.py
# This module is the "ears" of JARVIS.
# It does three things in sequence:
#   1. Listens continuously for the wake word "hey jarvis" using openwakeword
#   2. Records audio from the microphone after wake word is detected
#   3. Transcribes that audio to text using OpenAI Whisper (GPU accelerated)

import pyaudio
import numpy as np
import whisper
import wave
import tempfile
import os
import time
from openwakeword.model import Model as WakeWordModel

# ── Configuration ────────────────────────────────────────────────────────────

WAKE_WORD_MODEL   = "hey_jarvis"   # openwakeword built-in model name
WAKE_THRESHOLD    = 0.5            # confidence score to trigger (0.0 - 1.0)
SAMPLE_RATE       = 16000          # 16kHz — required by both whisper and openwakeword
CHANNELS          = 1              # mono audio
CHUNK             = 1280           # frames per buffer (80ms at 16kHz) — openwakeword default
RECORD_SECONDS    = 6              # how long to record after wake word (seconds)
WHISPER_MODEL     = "base"         # whisper model size: tiny/base/small/medium/large
DEVICE            = "cuda"         # use GPU; falls back to "cpu" if cuda unavailable

# ── JarvisListener Class ─────────────────────────────────────────────────────

class JarvisListener:
    def __init__(self):
        print("[LISTENER] Initializing listener...")

        # Load Whisper speech-to-text model onto GPU
        print(f"[LISTENER] Loading Whisper '{WHISPER_MODEL}' model on {DEVICE}...")
        try:
            self.whisper_model = whisper.load_model(WHISPER_MODEL, device=DEVICE)
            print(f"[LISTENER] Whisper loaded on {DEVICE} ✅")
        except Exception as e:
            # If GPU fails, fall back to CPU
            print(f"[LISTENER] GPU load failed ({e}), falling back to CPU...")
            self.whisper_model = whisper.load_model(WHISPER_MODEL, device="cpu")
            print("[LISTENER] Whisper loaded on CPU ✅")

        # Load openwakeword model for "hey jarvis" detection
        print("[LISTENER] Loading wake word model...")
        try:
            self.wake_model = WakeWordModel(
                wakeword_models=[WAKE_WORD_MODEL],
                inference_framework="onnx"
            )
            print("[LISTENER] Wake word model loaded ✅")
        except Exception as e:
            print(f"[LISTENER] Wake word model error: {e}")
            raise

        # Set up PyAudio for microphone input
        self.audio = pyaudio.PyAudio()
        print("[LISTENER] Ready.")

    def _open_stream(self):
        """Open a fresh PyAudio microphone stream."""
        return self.audio.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

    def wait_for_wake_word(self):
        """
        Continuously listens to the microphone.
        Returns only when 'hey jarvis' is detected with enough confidence.
        """
        print("[LISTENER] Waiting for wake word... (say 'Hey JARVIS')")
        stream = self._open_stream()

        try:
            while True:
                # Read one chunk of audio from microphone
                audio_chunk = stream.read(CHUNK, exception_on_overflow=False)

                # Convert raw bytes to int16 numpy array (required by openwakeword)
                audio_np = np.frombuffer(audio_chunk, dtype=np.int16)

                # Run wake word detection on this chunk
                prediction = self.wake_model.predict(audio_np)

                # prediction is a dict like {"hey_jarvis": 0.87}
                score = prediction.get(WAKE_WORD_MODEL, 0.0)

                # If confidence is high enough, wake word detected
                if score >= WAKE_THRESHOLD:
                    print(f"[LISTENER] Wake word detected! (confidence: {score:.2f})")
                    break

        finally:
            stream.stop_stream()
            stream.close()

    def record_command(self):
        """
        Records audio for RECORD_SECONDS after wake word is detected.
        Returns the audio as a numpy float32 array (what Whisper expects).
        """
        print(f"[LISTENER] Recording for {RECORD_SECONDS} seconds... speak now!")
        stream = self._open_stream()
        frames = []

        total_chunks = int(SAMPLE_RATE / CHUNK * RECORD_SECONDS)

        for i in range(total_chunks):
            audio_chunk = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(audio_chunk)

        stream.stop_stream()
        stream.close()
        print("[LISTENER] Recording done.")

        # Combine all chunks into one raw audio bytes object
        raw_audio = b"".join(frames)

        # Convert to float32 numpy array, normalized to [-1.0, 1.0]
        # Whisper expects float32 audio, not raw int16 bytes
        audio_np = np.frombuffer(raw_audio, dtype=np.int16).astype(np.float32) / 32768.0

        return audio_np

    def transcribe(self, audio_np):
        """
        Runs Whisper on the recorded audio and returns transcribed text.
        audio_np: float32 numpy array of audio samples
        """
        print("[LISTENER] Transcribing...")

        # Whisper transcribe — fp16=True uses faster half-precision on GPU
        result = self.whisper_model.transcribe(audio_np, fp16=(DEVICE == "cuda"))
        text = result["text"].strip()

        print(f"[LISTENER] You said: '{text}'")
        return text

    def listen(self):
        """
        Full pipeline: wait for wake word → record → transcribe.
        Returns the transcribed command string.
        This is the main method called by main.py.
        """
        self.wait_for_wake_word()
        audio = self.record_command()
        return self.transcribe(audio)

    def cleanup(self):
        """Release PyAudio resources cleanly on shutdown."""
        self.audio.terminate()
        print("[LISTENER] Cleaned up audio resources.")


# ── Standalone Test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    listener = JarvisListener()
    print("\n[TEST] Starting full listen cycle. Say 'Hey JARVIS' followed by a command.")
    
    try:
        while True:
            command = listener.listen()
            print(f"\n[TEST] Transcribed command: '{command}'")
            print("[TEST] Listening again...\n")
    except KeyboardInterrupt:
        print("\n[TEST] Stopped by user.")
        listener.cleanup()