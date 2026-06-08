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

def get_terminal_memory():
    """Calculates memory usage for each unique terminal session."""
    terminals = {}
    
    for proc in psutil.process_iter(['name', 'terminal', 'memory_info', 'ppid']):
        try:
            terminal = proc.info['terminal']
            if terminal and 'pts/' in terminal:
                if terminal not in terminals:
                    terminals[terminal] = {'usage': 0, 'apps': []}
                
                terminals[terminal]['usage'] += proc.info['memory_info'].rss / (1024 * 1024)
                
                # Try to identify the "active" app (not the shell)
                name = proc.info['name']
                if name not in ['bash', 'zsh', 'sh', 'fish', 'gnome-terminal-']:
                    terminals[terminal]['apps'].append(name)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
            
    # Format the results
    results = {}
    for tty, data in terminals.items():
        # Clean up app names to find the most relevant one
        active_apps = [a for a in data['apps'] if a]
        app_label = active_apps[-1] if active_apps else "Idle"
        results[f"Terminal ({tty.split('/')[-1]}) [{app_label}]"] = data['usage']
        
    return results

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
            terminal_info = get_terminal_memory()
            
            # Combine all monitoring data
            all_apps = {**app_info, **terminal_info}
                
            # Clear screen (ANSI escape code)
            print("\033[H\033[J", end="")
            print("--- Real-Time RAM Monitor (Linux) ---")
            print(f"Total:     {system_info['total']:>8} MB")
            print(f"Used:      {system_info['used']:>8} MB")
            print(f"Available: {system_info['available']:>8} MB")
            print(f"Usage:     {system_info['percent']:>8.1f}%")
            
            print("\n--- Application Usage ---")
            print(f"{'App':<30} {'Usage':>10} {'% of Total':>12}")
            for app, usage in all_apps.items():
                if usage > 0.1: # Show apps using more than 0.1 MB
                    app_percent = (usage / system_info['total'] * 100) if system_info['total'] > 0 else 0
                    print(f"{app:<30} {usage:>8.1f} MB {app_percent:>11.1f}%")
            
            print("\nPress Ctrl+C to exit.")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()
