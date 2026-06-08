import time
import os

def get_ram_info():
    """Reads /proc/meminfo and returns memory stats in MB."""
    meminfo = {}
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    # Value is usually something like "7956180 kB"
                    value_parts = parts[1].strip().split()
                    if value_parts:
                        value = value_parts[0]
                        meminfo[key] = int(value) // 1024  # Convert kB to MB
    except FileNotFoundError:
        print("Error: /proc/meminfo not found. This script is intended for Linux.")
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

def main():
    try:
        while True:
            info = get_ram_info()
            if info is None:
                break
                
            # Clear screen (ANSI escape code)
            print("\033[H\033[J", end="")
            print("--- Real-Time RAM Monitor (Linux) ---")
            print(f"Total:     {info['total']:>8} MB")
            print(f"Used:      {info['used']:>8} MB")
            print(f"Available: {info['available']:>8} MB")
            print(f"Usage:     {info['percent']:>8.1f}%")
            print("\nPress Ctrl+C to exit.")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()
