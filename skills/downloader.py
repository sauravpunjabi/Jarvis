import os
import yt_dlp
from tqdm import tqdm

# The Downloader module handles downloading media using yt-dlp with progress indicators.

class DownloaderSkill:
    def __init__(self):
        print("[DOWNLOADER] Downloader module initialized.")
        self.downloads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "downloads")
        os.makedirs(self.downloads_dir, exist_ok=True)
        
    class _TqdmUpTo(tqdm):
        """Provides progress bar for yt-dlp using tqdm."""
        def update_to(self, d):
            if d['status'] == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded_bytes = d.get('downloaded_bytes', 0)
                
                if total_bytes:
                    self.total = total_bytes
                self.update(downloaded_bytes - self.n)

    def download_video(self, url: str) -> str:
        """Downloads a video from a URL using yt-dlp."""
        print(f"[DOWNLOADER] Initiating download for: {url}")
        
        # Confirmation check (simulated via the planner but explicitly handled here)
        user_input = input(f"Sir, are you sure you want to download from {url}? (y/n): ").strip().lower()
        if user_input != 'y':
            return "Download cancelled, sir."
            
        output_template = os.path.join(self.downloads_dir, "%(title)s.%(ext)s")
        
        ydl_opts = {
            'outtmpl': output_template,
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
        }

        try:
            print("[DOWNLOADER] Downloading... Please wait.")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'video')
                
            return f"Successfully downloaded '{title}' to the downloads folder, sir."
        except Exception as e:
            print(f"[DOWNLOADER] Error during download: {e}")
            return "I encountered an error while trying to download the file, sir."

if __name__ == "__main__":
    downloader = DownloaderSkill()
    # To test interactively, uncomment below:
    # print(downloader.download_video("https://www.youtube.com/watch?v=BaW_jenozKc"))
