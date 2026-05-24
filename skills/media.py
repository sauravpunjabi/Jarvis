import os
import subprocess
import webbrowser
import pyautogui
import time
import yt_dlp

# The Media module handles Spotify integration, global media controls,
# and YouTube playback using yt-dlp (download and play audio).

class MediaSkill:
    def __init__(self):
        print("[MEDIA] Media module initialized.")
        self.downloads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "downloads")
        os.makedirs(self.downloads_dir, exist_ok=True)

    def play_pause(self) -> str:
        """Toggles play/pause for the system media."""
        print("[MEDIA] Toggling play/pause")
        pyautogui.press("playpause")
        return "Toggling playback, sir."

    def next_track(self) -> str:
        """Skips to the next track."""
        print("[MEDIA] Next track")
        pyautogui.press("nexttrack")
        return "Skipping to the next track, sir."

    def prev_track(self) -> str:
        """Goes back to the previous track."""
        print("[MEDIA] Previous track")
        pyautogui.press("prevtrack")
        return "Playing the previous track, sir."
        
    def stop_media(self) -> str:
        """Stops the media playback."""
        print("[MEDIA] Stopping media")
        pyautogui.press("stop")
        return "Stopping playback, sir."

    def open_spotify(self) -> str:
        """Launches Spotify app."""
        print("[MEDIA] Opening Spotify...")
        try:
            # On Windows 11, Spotify URI can launch the app directly
            os.startfile("spotify:")
            return "Opening Spotify now, sir."
        except Exception as e:
            print(f"[MEDIA] Failed to open Spotify via URI: {e}")
            try:
                # Fallback to AppData path if available
                appdata = os.getenv("APPDATA")
                spotify_path = os.path.join(appdata, "Spotify", "Spotify.exe")
                if os.path.exists(spotify_path):
                    subprocess.Popen([spotify_path])
                    return "Opening Spotify now, sir."
                else:
                    return "I am unable to locate Spotify on this system, sir."
            except Exception as e2:
                print(f"[MEDIA] Fallback Spotify launch failed: {e2}")
                return "I encountered an error trying to open Spotify, sir."

    def play_youtube_audio(self, search_query: str) -> str:
        """
        Uses yt-dlp to search YouTube, download the best audio format as an mp3, 
        and plays it using the default system player.
        """
        print(f"[MEDIA] Searching YouTube for: {search_query}")
        
        # Define yt-dlp options
        output_template = os.path.join(self.downloads_dir, "%(title)s.%(ext)s")
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': output_template,
            'default_search': 'ytsearch1:', # Returns only the top 1 result
            'noplaylist': True,
            'quiet': False
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{search_query}", download=True)
                
                if 'entries' in info and len(info['entries']) > 0:
                    video_info = info['entries'][0]
                else:
                    video_info = info
                
                title = video_info.get('title', 'Unknown Title')
                print(f"[MEDIA] Downloaded audio for: {title}")
                
                # Finding the downloaded mp3 file
                mp3_files = [os.path.join(self.downloads_dir, f) for f in os.listdir(self.downloads_dir) if f.endswith('.mp3')]
                if not mp3_files:
                    return "I downloaded the file but could not find the mp3 format, sir."
                
                latest_file = max(mp3_files, key=os.path.getmtime)
                print(f"[MEDIA] Playing {latest_file}...")
                os.startfile(latest_file)
                
                return f"Playing {title} from YouTube, sir."
                
        except Exception as e:
            print(f"[MEDIA] Error with YouTube playback: {e}")
            return "I encountered an error while trying to play the YouTube audio, sir."


    def play_spotify_song(self, query: str) -> str:
        """Opens Spotify search for the given query."""
        print(f"[MEDIA] Searching Spotify for: {query}")
        try:
            os.startfile(f"spotify:search:{query}")
            return f"Searching Spotify for {query}, sir."
        except Exception:
            webbrowser.open(f"https://open.spotify.com/search/{query.replace(' ', '%20')}")
            return f"Opening Spotify search for {query} in browser, sir."

    def download_youtube(self, query: str, path: str = None) -> str:
        """Downloads a YouTube video/audio as mp3 to the given path (default: Desktop)."""
        if path is None:
            path = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")

        print(f"[MEDIA] Downloading: {query}")
        output_template = os.path.join(path, "%(title)s.%(ext)s")
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "outtmpl": output_template,
            "default_search": "ytsearch1:",
            "noplaylist": True,
            "quiet": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)
                entries = info.get("entries") or [info]
                title = entries[0].get("title", query)
            return f"Downloaded '{title}' to your Desktop, sir."
        except Exception as e:
            print(f"[MEDIA] Download error: {e}")
            return f"I encountered an error downloading that, sir."

    def get_volume(self) -> str:
        """Returns current system volume as a percentage."""
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            level = int(volume.GetMasterVolumeLevelScalar() * 100)
            return f"Volume is at {level} percent, sir."
        except Exception as e:
            return f"Couldn't read volume, sir. {e}"

    def set_volume(self, level: int) -> str:
        """Sets system volume to the given percentage (0–100)."""
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            scalar = max(0.0, min(1.0, level / 100))
            volume.SetMasterVolumeLevelScalar(scalar, None)
            return f"Volume set to {level} percent, sir."
        except Exception as e:
            return f"Couldn't set volume, sir. {e}"


if __name__ == "__main__":
    media = MediaSkill()
    
    # Test play/pause
    print(media.play_pause())
    time.sleep(2)
    
    # Test open spotify
    print(media.open_spotify())
    time.sleep(5)
    
    # Test youtube playback (Commented out to avoid downloading during simple run)
    # print(media.play_youtube_audio("interstellar main theme hans zimmer"))

