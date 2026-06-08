import time
import os
import psutil

def get_ram_info():
    """Reads /proc/meminfo and returns system-wide memory stats in MB."""
    meminfo = {}
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    value_parts = parts[1].strip().split()
                    if value_parts:
                        value = value_parts[0]
                        meminfo[key] = int(value) // 1024  # Convert kB to MB
    except FileNotFoundError:
        return None
    
    total = meminfo.get('MemTotal', 0)
    available = meminfo.get('MemAvailable', 0)
    used = total - available
    percent = (used / total * 100) if total > 0 else 0
    
    return {
        'total': total,
        'used': used,
        'available': available,
        'percent': percent
    }

def get_app_memory(app_patterns):
    """Calculates total RSS memory usage for apps matching patterns."""
    app_stats = {name: 0 for name in app_patterns}
    
    for proc in psutil.process_iter(['name', 'cmdline', 'memory_info']):
        try:
            cmdline = " ".join(proc.info['cmdline']) if proc.info['cmdline'] else ""
            for name, pattern in app_patterns.items():
                if pattern in cmdline or pattern in proc.info['name']:
                    app_stats[name] += proc.info['memory_info'].rss / (1024 * 1024)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
            
    return app_stats

def main():
    # Define search patterns for the requested apps
    apps_to_track = {
        'Gemini': '/bin/gemini',
        'VSCode': '/usr/share/code/code',
        'Brave': '/opt/brave.com/brave/brave'
    }

    try:
        while True:
            system_info = get_ram_info()
            if system_info is None:
                print("Error: Could not read system RAM info.")
                break
                
            app_info = get_app_memory(apps_to_track)
                
            # Clear screen (ANSI escape code)
            print("\033[H\033[J", end="")
            print("--- Real-Time RAM Monitor (Linux) ---")
            print(f"Total:     {system_info['total']:>8} MB")
            print(f"Used:      {system_info['used']:>8} MB")
            print(f"Available: {system_info['available']:>8} MB")
            print(f"Usage:     {system_info['percent']:>8.1f}%")
            
            print("\n--- Application Usage ---")
            for app, usage in app_info.items():
                if usage > 0:
                    print(f"{app:<10} {usage:>8.1f} MB")
            
            print("\nPress Ctrl+C to exit.")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()
