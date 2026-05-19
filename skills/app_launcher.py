import os
import glob
import subprocess
from pathlib import Path

# The App Launcher module handles finding and launching local Windows applications.

class AppLauncherSkill:
    def __init__(self):
        print("[PC] App Launcher module initialized.")
        # Common locations for shortcuts
        self.search_paths = [
            os.path.join(os.getenv("PROGRAMDATA", "C:\\ProgramData"), "Microsoft", "Windows", "Start Menu", "Programs"),
            os.path.join(os.getenv("APPDATA", "C:\\Users\\Default\\AppData\\Roaming"), "Microsoft", "Windows", "Start Menu", "Programs"),
            os.path.join(os.getenv("USERPROFILE", "C:\\Users\\Default"), "Desktop"),
            "C:\\Users\\Public\\Desktop"
        ]
        
    def _find_app(self, app_name: str) -> str | None:
        """Searches for a .lnk file matching the app name."""
        app_name_lower = app_name.lower().replace(" ", "")
        
        for base_path in self.search_paths:
            if not os.path.exists(base_path):
                continue
                
            # Recursively find all .lnk files
            for root, _, files in os.walk(base_path):
                for file in files:
                    if file.lower().endswith(".lnk"):
                        # Remove extension and spaces for comparison
                        name_without_ext = os.path.splitext(file)[0].lower().replace(" ", "")
                        if app_name_lower in name_without_ext or name_without_ext in app_name_lower:
                            return os.path.join(root, file)
        return None

    def launch_app(self, app_name: str) -> str:
        """Launches the specified application."""
        print(f"[PC] Attempting to launch: {app_name}")
        app_path = self._find_app(app_name)
        
        if app_path:
            try:
                # Use os.startfile for Windows shortcuts
                os.startfile(app_path)
                return f"Launching {os.path.basename(app_path).replace('.lnk', '')}, sir."
            except Exception as e:
                print(f"[PC] Error launching {app_path}: {e}")
                return f"I found {app_name}, but encountered an error launching it, sir."
                
        # Fallbacks for common apps that might be in PATH
        common_cmds = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "calc": "calc.exe",
            "cmd": "cmd.exe",
            "command prompt": "cmd.exe",
            "paint": "mspaint.exe",
            "explorer": "explorer.exe",
            "spotify": "spotify:"
        }
        
        if app_name.lower() in common_cmds:
            try:
                os.startfile(common_cmds[app_name.lower()])
                return f"Launching {app_name}, sir."
            except Exception:
                pass
                
        return f"I could not locate an application named {app_name} on your system, sir."

if __name__ == "__main__":
    launcher = AppLauncherSkill()
    print(launcher.launch_app("notepad"))
    print(launcher.launch_app("calculator"))
