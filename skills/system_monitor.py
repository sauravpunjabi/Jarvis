import psutil
import GPUtil
import platform
import time

# The System Monitor module provides real-time analytics on CPU, RAM, Disk, GPU, and Battery.

class SystemMonitorSkill:
    def __init__(self):
        print("[PC] System Monitor initialized.")
        self.boot_time = psutil.boot_time()

    def get_system_stats(self) -> dict:
        """Gathers system statistics and returns them as a dictionary."""
        stats = {}
        
        # CPU
        stats['cpu_percent'] = psutil.cpu_percent(interval=0.5)
        stats['cpu_count'] = psutil.cpu_count(logical=True)
        
        # RAM
        ram = psutil.virtual_memory()
        stats['ram_total_gb'] = round(ram.total / (1024**3), 2)
        stats['ram_used_gb'] = round(ram.used / (1024**3), 2)
        stats['ram_percent'] = ram.percent
        
        # Disk (C: drive)
        try:
            disk = psutil.disk_usage('C:\\')
            stats['disk_total_gb'] = round(disk.total / (1024**3), 2)
            stats['disk_free_gb'] = round(disk.free / (1024**3), 2)
            stats['disk_percent'] = disk.percent
        except Exception:
            pass
            
        # GPU
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                stats['gpu_name'] = gpus[0].name
                stats['gpu_load'] = round(gpus[0].load * 100, 1)
                stats['gpu_memory_total'] = gpus[0].memoryTotal
                stats['gpu_memory_used'] = gpus[0].memoryUsed
            else:
                stats['gpu_name'] = "None detected"
        except Exception:
            stats['gpu_name'] = "GPUtil error"
            
        # Battery
        try:
            battery = psutil.sensors_battery()
            if battery:
                stats['battery_percent'] = battery.percent
                stats['power_plugged'] = battery.power_plugged
            else:
                stats['battery_percent'] = "No battery"
        except Exception:
            pass
            
        # Uptime
        uptime_seconds = time.time() - self.boot_time
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        stats['uptime'] = f"{int(hours)}h {int(minutes)}m"
        
        return stats

    def report_status(self) -> str:
        """Returns a formatted human-readable system status report."""
        print("[PC] Gathering system status...")
        stats = self.get_system_stats()
        
        report = []
        report.append(f"CPU usage is at {stats.get('cpu_percent', 0)}%.")
        report.append(f"RAM usage is {stats.get('ram_used_gb', 0)} GB out of {stats.get('ram_total_gb', 0)} GB ({stats.get('ram_percent', 0)}%).")
        
        if 'battery_percent' in stats and isinstance(stats['battery_percent'], (int, float)):
            plug_status = "plugged in" if stats.get('power_plugged') else "on battery"
            report.append(f"Battery is at {stats['battery_percent']}%, {plug_status}.")
            
        if 'gpu_name' in stats and stats['gpu_name'] not in ["None detected", "GPUtil error"]:
            report.append(f"GPU ({stats['gpu_name']}) load is at {stats.get('gpu_load', 0)}%.")
            
        report.append(f"System uptime is {stats.get('uptime', 'unknown')}.")
        
        return " ".join(report)

if __name__ == "__main__":
    monitor = SystemMonitorSkill()
    print("\n--- System Status Report ---")
    print(monitor.report_status())
