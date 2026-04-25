#lets jarvis control pc via commands.

from ast import Import
from asyncio import subprocess
import os
import subprocess
import psutil
import ctypes
from datetime import datetime

#a list of operations im adding to check if it will work

APP_MAP ={
    "brave": "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
    "whatsapp": "WhatsApp.exe",
    "spotify": "Spotify.exe",
    "notepad": "notepad.exe",
    "discord": "discord.exe",
    "paint": "mspaint.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
}

class PcController:
    def __init__(self):
        print("[PC] PC controller initialized.")

    #to open applications
    def open_app(self, app_name: str) -> str:
        """opens an application by name"""
        name = app_name.lower().strip()

        if name in APP_MAP:
            exe = APP_MAP[name]
            try:
                subprocess.Popen(exe, shell=True)
                return f"Opening {app_name}, sir."
            except Exception as e:
                return f"I couldnt open {app_name}, sir.  Error: {e}"
        else:
            try:
                subprocess.Popen(app_name, shell=True)
                return f"Attempting to open {app_name}, sir."
            except Exception as e:
                return f"I dont know how to open {app_name}, sir."

    #to control volume
    def volume_up(self) -> str:
        """Increase the volume with UP key"""
        try: 
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudiioUtilities, IAudioEndpointVolume
            import math

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))

            current = volume.GetMasterVolumeLevel()
            new_vol = min(1.0, current + 0.1) #increase by 10%
            volume.SetMasterVolumeLevel(new_vol, None)
            return f"Volume increased to {int(new_vol * 100)} percent, sir."
        except ImportError:
            import subprocess
            subprocess.run(["powershell", "-c",
                "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"], 
                capture_output=True)
            return f"Volume increased, sir."
        
        except Exception as e:
            return f"Couldnt change volume, sir. Error: {e}"

    #to decrease volume
    def volume_down(self) -> str:
        """decrease the volume with down key"""
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))

            current = volume.GetMasterVolumeLevel()
            new_vol = max(0.0, current - 0.1)
            volume.SetMasterVolumeLevel(new_vold, None)
            return f"Volume decreased to {int(new_vol * 100)} percent, sir."
        except ImportError:
            subprocess.run(["powershell", "-c",
                "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"],
                capture_output=True)
            return f"Volume decreased, sir."
        except Exception as e:
            return f"Couldnt decrease volume, sir. Error: {e}"

    #to go mute
    def mute(self) -> str:
        """Toggles mute on/off."""
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))

            is_muted = volume.GetMute()
            volume.SetMute(not is_muted, None)
            state = "Muted" if not is_muted else "Unmuted"
            return f"{state}, sir."
        except ImportError:
            subprocess.run(["powershell", "-c",
                "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"],
                capture_output=True)
            return "Toggled mute, sir."
        except Exception as e:
            return f"Couldn't toggle mute, sir. {e}"

    #battery
    def get_battery(self) -> str:
        """Returns current battery percentage and charging status."""
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return "I couldn't read the battery status, sir."
            percent = int(battery.percent)
            charging = battery.power_plugged
            status = "charging" if charging else "not charging"
            return f"Battery is at {percent} percent and {status}, sir."
        except Exception as e:
            return f"Couldn't read battery, sir. {e}"
        
    #system controls
    def lock_computer(self) -> str:
        """Locks the Windows screen."""
        try:
            ctypes.windll.user32.LockWorkStation()
            return "Locking your workstation, sir."
        except Exception as e:
            return f"Couldn't lock the computer, sir. {e}"

    def shutdown(self) -> str:
        """Shuts down the computer after 10 seconds."""
        try:
            os.system("shutdown /s /t 10")
            return "Shutting down in 10 seconds, sir. Goodbye."
        except Exception as e:
            return f"Couldn't initiate shutdown, sir. {e}"

    def restart(self) -> str:
        """Restarts the computer after 10 seconds."""
        try:
            os.system("shutdown /r /t 10")
            return "Restarting in 10 seconds, sir."
        except Exception as e:
            return f"Couldn't restart, sir. {e}"

    def cancel_shutdown(self) -> str:
        """Cancels a pending shutdown or restart."""
        os.system("shutdown /a")
        return "Shutdown cancelled, sir."

    #Screenshot
    def take_screenshot(self) -> str:
        """Takes a screenshot and saves it to the Desktop."""
        try:
            import PIL.ImageGrab as ImageGrab
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", f"jarvis_screenshot_{timestamp}.png")
            screenshot = ImageGrab.grab()
            screenshot.save(path)
            return f"Screenshot saved to your Desktop, sir."
        except ImportError:
            # Fallback using PowerShell if PIL not available
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", f"jarvis_screenshot_{timestamp}.png")
            subprocess.run([
                "powershell", "-c",
                f"Add-Type -AssemblyName System.Windows.Forms; "
                f"[System.Windows.Forms.Screen]::PrimaryScreen | Out-Null; "
                f"$b = [System.Drawing.Bitmap]::new([System.Windows.Forms.SystemInformation]::PrimaryMonitorSize.Width, "
                f"[System.Windows.Forms.SystemInformation]::PrimaryMonitorSize.Height); "
                f"$g = [System.Drawing.Graphics]::FromImage($b); "
                f"$g.CopyFromScreen(0,0,0,0,$b.Size); "
                f"$b.Save('{path}')"
            ], capture_output=True)
            return f"Screenshot saved to your Desktop, sir."
        except Exception as e:
            return f"Couldn't take screenshot, sir. {e}"
    

    #System stats
    def get_system_stats(self) -> str:
        """Returns CPU, RAM, and battery info."""
        try:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            battery = psutil.sensors_battery()
            bat_str = f", battery at {int(battery.percent)} percent" if battery else ""
            return f"CPU is at {cpu} percent, RAM at {ram} percent{bat_str}, sir."
        except Exception as e:
            return f"Couldn't read system stats, sir. {e}"
    
    #standalone test
if __name__ == "__main__":
    pc = PcController()

    print("\n--- Battery ---")
    print(pc.get_battery())

    print("\n--- System Stats ---")
    print(pc.get_system_stats())

    print("\n--- Screenshot ---")
    print(pc.take_screenshot())

    print("\n--- Open spotify ---")
    print(pc.open_app("spotify"))