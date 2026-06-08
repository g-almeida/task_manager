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

def get_all_usage(tracked_patterns):
    """Gathers memory usage for tracked apps, terminals, and top 3 others."""
    tracked_stats = {name: 0 for name in tracked_patterns}
    terminal_stats = {}
    other_stats = {}
    
    for proc in psutil.process_iter(['name', 'cmdline', 'terminal', 'memory_info']):
        try:
            info = proc.info
            usage_mb = info['memory_info'].rss / (1024 * 1024)
            if usage_mb == 0:
                continue

            terminal = info['terminal']
            cmdline = " ".join(info['cmdline']) if info['cmdline'] else ""
            name = info['name']

            # 1. Check Terminal Session
            if terminal and 'pts/' in terminal:
                if terminal not in terminal_stats:
                    terminal_stats[terminal] = {'usage': 0, 'apps': []}
                terminal_stats[terminal]['usage'] += usage_mb
                if name not in ['bash', 'zsh', 'sh', 'fish', 'gnome-terminal-']:
                    terminal_stats[terminal]['apps'].append(name)
                continue

            # 2. Check Tracked Apps
            is_tracked = False
            for label, pattern in tracked_patterns.items():
                if pattern in cmdline or pattern in name:
                    tracked_stats[label] += usage_mb
                    is_tracked = True
                    break
            
            if is_tracked:
                continue

            # 3. Otherwise, it's an "Other" app
            other_stats[name] = other_stats.get(name, 0) + usage_mb

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Format the results into a single list
    combined_results = []

    # Add Tracked Apps
    for label, usage in tracked_stats.items():
        if usage > 0.1:
            combined_results.append((label, usage))

    # Add Terminals
    for tty, data in terminal_stats.items():
        active_apps = [a for a in data['apps'] if a]
        app_label = active_apps[-1] if active_apps else "Idle"
        label = f"Terminal ({tty.split('/')[-1]}) [{app_label}]"
        combined_results.append((label, data['usage']))

    # Add Top 3 Others
    sorted_others = sorted(other_stats.items(), key=lambda x: x[1], reverse=True)
    for name, usage in sorted_others[:3]:
        if usage > 0.1:
            combined_results.append((f"[Top] {name}", usage))

    # Final Sort by usage descending
    combined_results.sort(key=lambda x: x[1], reverse=True)

    return combined_results

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
                
            all_usage = get_all_usage(apps_to_track)
                
            # Clear screen (ANSI escape code)
            print("\033[H\033[J", end="")
            print("--- Real-Time RAM Monitor (Linux) ---")
            print(f"Total:     {system_info['total']:>8} MB")
            print(f"Used:      {system_info['used']:>8} MB")
            print(f"Available: {system_info['available']:>8} MB")
            print(f"Usage:     {system_info['percent']:>8.1f}%")
            
            print("\n--- Application Usage (Sorted) ---")
            print(f"{'App':<30} {'Usage':>10} {'% of Total':>12}")
            for label, usage in all_usage:
                app_percent = (usage / system_info['total'] * 100) if system_info['total'] > 0 else 0
                print(f"{label:<30} {usage:>8.1f} MB {app_percent:>11.1f}%")
            
            print("\nPress Ctrl+C to exit.")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()
