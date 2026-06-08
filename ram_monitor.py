import time
import os
import psutil
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

@dataclass
class MemoryStats:
    """Container for system-wide memory statistics."""
    total: int
    used: int
    available: int
    percent: float

@dataclass
class AppUsage:
    """Container for individual application memory usage."""
    label: str
    usage_mb: float
    percent_of_total: float

class MemoryDataCollector:
    """Handles the extraction of memory data from the system and processes."""
    
    def __init__(self, tracked_patterns: Dict[str, str]):
        self.tracked_patterns = tracked_patterns

    def get_system_stats(self) -> Optional[MemoryStats]:
        """Reads /proc/meminfo to get system-wide RAM stats."""
        meminfo = {}
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if ':' not in line:
                        continue
                    key, value = line.split(':', 1)
                    parts = value.strip().split()
                    if parts:
                        # Convert kB to MB
                        meminfo[key.strip()] = int(parts[0]) // 1024
        except (FileNotFoundError, PermissionError, ValueError):
            return None

        total = meminfo.get('MemTotal', 0)
        available = meminfo.get('MemAvailable', 0)
        used = total - available
        percent = (used / total * 100) if total > 0 else 0
        
        return MemoryStats(total, used, available, percent)

    def collect_all_usage(self, system_total_mb: int) -> List[AppUsage]:
        """Gathers and categorizes usage for tracked apps, terminals, and top consumers."""
        tracked_usage = {name: 0.0 for name in self.tracked_patterns}
        terminal_usage = {}
        other_usage = {}

        for proc in psutil.process_iter(['name', 'cmdline', 'terminal', 'memory_info']):
            try:
                info = proc.info
                # Resident Set Size (RSS) is the actual physical memory used
                usage_mb = info['memory_info'].rss / (1024 * 1024)
                if usage_mb < 0.1:
                    continue

                # 1. Terminal Session Logic
                tty = info['terminal']
                if tty and 'pts/' in tty:
                    if tty not in terminal_usage:
                        terminal_usage[tty] = {'usage': 0.0, 'apps': []}
                    terminal_usage[tty]['usage'] += usage_mb
                    if info['name'] not in ['bash', 'zsh', 'sh', 'fish', 'gnome-terminal-']:
                        terminal_usage[tty]['apps'].append(info['name'])
                    continue

                # 2. Tracked Application Logic
                cmdline = " ".join(info['cmdline']) if info['cmdline'] else ""
                matched_tracked = False
                for label, pattern in self.tracked_patterns.items():
                    if pattern in cmdline or pattern in info['name']:
                        tracked_usage[label] += usage_mb
                        matched_tracked = True
                        break
                
                if matched_tracked:
                    continue

                # 3. General Application Logic
                name = info['name']
                other_usage[name] = other_usage.get(name, 0.0) + usage_mb

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return self._format_and_sort_results(tracked_usage, terminal_usage, other_usage, system_total_mb)

    def _format_and_sort_results(self, tracked: dict, terminals: dict, others: dict, total_mb: int) -> List[AppUsage]:
        results = []

        # Process Tracked Apps
        for label, usage in tracked.items():
            if usage > 0.1:
                results.append(AppUsage(label, usage, (usage / total_mb * 100)))

        # Process Terminal Sessions
        for tty, data in terminals.items():
            active_apps = [a for a in data['apps'] if a]
            app_label = active_apps[-1] if active_apps else "Idle"
            label = f"Terminal ({tty.split('/')[-1]}) [{app_label}]"
            results.append(AppUsage(label, data['usage'], (data['usage'] / total_mb * 100)))

        # Process Top 3 Others
        sorted_others = sorted(others.items(), key=lambda x: x[1], reverse=True)
        for name, usage in sorted_others[:3]:
            results.append(AppUsage(f"[Top] {name}", usage, (usage / total_mb * 100)))

        # Sort all results by usage descending
        results.sort(key=lambda x: x.usage_mb, reverse=True)
        return results

class DisplayManager:
    """Handles terminal output formatting."""
    
    @staticmethod
    def clear_screen():
        print("\033[H\033[J", end="")

    def render(self, system: MemoryStats, apps: List[AppUsage]):
        self.clear_screen()
        print("--- Real-Time RAM Monitor (Linux) ---")
        print(f"{'Total:':<12} {system.total:>8} MB")
        print(f"{'Used:':<12} {system.used:>8} MB")
        print(f"{'Available:':<12} {system.available:>8} MB")
        print(f"{'Usage:':<12} {system.percent:>8.1f}%")
        
        print("\n--- Application Usage (Sorted) ---")
        print(f"{'App':<30} {'Usage':>10} {'% of Total':>12}")
        for app in apps:
            print(f"{app.label:<30} {app.usage_mb:>8.1f} MB {app.percent_of_total:>11.1f}%")
        
        print("\nPress Ctrl+C to exit.")

def main():
    tracked_apps = {
        'Gemini': '/bin/gemini',
        'VSCode': '/usr/share/code/code',
        'Brave': '/opt/brave.com/brave/brave'
    }

    collector = MemoryDataCollector(tracked_apps)
    display = DisplayManager()

    try:
        while True:
            system_stats = collector.get_system_stats()
            if not system_stats:
                print("Error: Could not access system memory data.")
                break
                
            app_usage = collector.collect_all_usage(system_stats.total)
            display.render(system_stats, app_usage)
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting monitor...")

if __name__ == "__main__":
    main()
