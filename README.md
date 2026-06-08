# Real-Time RAM Monitor for Linux

A Python-based utility to monitor system-wide and application-specific memory usage in real-time, with auto-restart capabilities.

## Architecture & Code Structure

The application is built with a clear separation of concerns, divided into two main components: the **Monitor** and the **Watcher**.

### 1. `ram_monitor.py` (The Core Engine)
This script is responsible for data collection and display. It is structured into three main layers:

- **Data Containers (`dataclasses`)**: 
    - `MemoryStats`: Stores system-level data (Total, Used, Available, %).
    - `AppUsage`: Stores per-process data (Label, MB, % of Total).
- **`MemoryDataCollector` Class**: 
    - **System Stats**: Directly parses `/proc/meminfo`. This is the most efficient way to get "ground truth" memory data on Linux without external dependencies.
    - **Process Stats**: Uses `psutil` to iterate through all running processes. It categorizes them into Tracked Apps (Gemini, VSCode, Brave), Terminal Sessions (grouped by TTY), and the "Top 3" most intensive remaining processes.
    - **RSS Memory**: The script tracks **Resident Set Size (RSS)**, which represents the actual physical memory occupied by a process.
- **`DisplayManager` Class**: 
    - Handles ANSI escape codes to clear the terminal and renders the collected data in a clean, sorted table.

### 2. `watch.py` (Development Utility)
Uses the `watchdog` library to observe the project directory. If `ram_monitor.py` is modified, the watcher kills the current process and spawns a new one, allowing for a seamless development experience.

---

## Permissions & Data Access

### System Memory (`/proc/meminfo`)
- **Permission**: On most Linux distributions, `/proc/meminfo` is world-readable (`644`).
- **Access**: The script reads this file directly. No elevated privileges (sudo) are required to see general system memory stats.

### Process Information (`/proc/[pid]`)
- **Permission**: Linux restricts access to some process details for security.
- **Access Model**:
    - **Owned Processes**: You can always see full details for processes you started (e.g., your browser, VS Code, other terminals).
    - **Other Users/System**: `psutil` may encounter `AccessDenied` errors when trying to read detailed memory info for processes owned by `root` or other users.
- **Error Handling**: The `MemoryDataCollector` is designed to gracefully catch `psutil.AccessDenied` exceptions. It simply skips processes it doesn't have permission to inspect, ensuring the monitor continues to run for the apps it *can* see.
- **Elevated Privileges**: While not required, running the monitor with `sudo` would allow it to see the memory usage of *all* system processes, including those owned by the kernel or root.

---

## How to Run

1. **Install Dependencies**:
   ```bash
   poetry install
   ```

2. **Standard Run**:
   ```bash
   poetry run monitor
   ```

3. **Development Mode (Auto-Restart)**:
   ```bash
   poetry run watch
   ```
