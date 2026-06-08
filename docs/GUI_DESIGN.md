# GUI Design and Implementation Details

This document explains the technical implementation and design choices for the RAM Monitor GUI.

## 1. Choice of Framework: PySide6 (Qt for Python)
While the initial plan considered Tkinter for its simplicity, we switched to **PySide6** because:
- **Feature Rich**: It provides professional-grade widgets like `QTreeWidget` with better performance for dynamic updates.
- **Native Look**: It better integrates with modern Linux desktop environments.
- **Scalability**: Qt's layout system is more robust for handling window resizing.

## 2. Structural Design (The "Skeleton")
The GUI follows a vertical hierarchy managed by `QVBoxLayout`:

### A. System Statistics (Header)
- **Component**: `QGroupBox` titled "System Statistics".
- **Layout**: `QHBoxLayout` (Horizontal).
- **Widgets**: Four `QLabel` widgets.
- **Logic**: These labels are updated every second with global data from `/proc/meminfo`. Placing them at the top provides an immediate "health check" of the system.

### B. Application Table (Body)
- **Component**: `QGroupBox` titled "Application Usage (Sorted)".
- **Layout**: `QVBoxLayout`.
- **Widget**: `QTreeWidget`.
- **Column Design**:
    - **Application Name**: Left-aligned, occupies 250px by default to handle long process names or terminal labels.
    - **Usage (MB)**: Right-aligned for easy numerical comparison.
    - **% of Total**: Right-aligned, providing relative context.

## 3. The Real-Time Update Mechanism
The GUI does not "wait" for data, which would freeze the window. Instead, it uses **Asynchronous Timing**:

1. **`QTimer`**: A non-blocking timer is initialized in the constructor.
2. **Timeout**: Every 1000ms (1 second), the timer triggers the `update_data()` method.
3. **Data Refresh**:
    - `MemoryDataCollector` fetches the latest system and process stats.
    - The `QTreeWidget` is cleared and repopulated with the new sorted list.
    - Label texts are updated.

## 4. Design for Sorting
The decision was made to perform sorting at the **Data Layer** (inside `MemoryDataCollector`) rather than the **UI Layer**.
- **Reason**: By sorting the list in Python before it hits the GUI, we ensure that the "Top 3" logic and the "Tracked App" logic are combined correctly before display.
- **Visual Result**: The app with the highest memory usage always jumps to the top of the table.

## 5. Deployment (PyInstaller)
The design includes a `.spec` configuration (managed by PyInstaller) that bundles the Qt shared libraries.
- **Windowed Mode**: The `--windowed` flag ensures that no terminal pops up when launching the GUI binary.
- **Onefile**: Compresses everything into a single executable for easy distribution.
