# GUI and Executable Transition Plan

## Objective
Transition the RAM monitor from a CLI tool to a GUI application and create a standalone executable for Linux.

## Proposed Solution
- **GUI Framework**: Use `Tkinter` (Python's built-in GUI library) for a simple, cross-platform-ready interface.
- **Executable Builder**: Use `PyInstaller` to bundle the script and dependencies into a single binary.

## Implementation Steps
1.  **Dependencies**: Add `pyinstaller` to the Poetry environment.
2.  **GUI Development (`ram_monitor_gui.py`)**:
    - Reuse `MemoryDataCollector` and `MemoryStats`/`AppUsage` classes.
    - Build a main window with labels for system stats.
    - Add a `ttk.Treeview` (table) to display sorted application usage.
    - Implement a recurring update loop using `root.after()`.
3.  **Project Configuration**:
    - Add `gui-monitor` to `pyproject.toml` scripts.
4.  **Build Process**:
    - Run `pyinstaller --onefile --windowed ram_monitor_gui.py`.
    - Verify the resulting binary in the `dist/` directory.

## Verification
- Run the GUI script via Poetry.
- Run the generated executable from the terminal and verify functionality.
