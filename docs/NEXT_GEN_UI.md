# RAM Monitor: Next-Gen Native Linux UI Transformation

## Vision
Transform the current performance monitor into a professional, native Linux application using **GTK4** and **libadwaita**. This will replace the generic PySide6 interface with a UI that follows modern Linux design patterns (Gnome-style), offering deep system integration, adaptive layouts, and a "Glassmorphism" aesthetic.

## Why GTK4 + libadwaita?
- **Native Performance**: Uses the GPU for all rendering (GSK), ensuring smooth 60fps animations for real-time graphs.
- **System Integration**: Inherits the user's system accent color and dark/light mode automatically.
- **Modern Components**: Provides high-end widgets like `Adw.StatusPage`, `Adw.HeaderBar`, and `Adw.ActionRow` out of the box.

## Design Concept
- **Glassmorphism**: Use custom CSS within GTK to create semi-transparent backgrounds with background blur (where supported by the compositor).
- **Dynamic Charts**: Add a real-time "Pulse" line chart for total RAM usage using `Cairo` or `Graphene` drawing.
- **Theming**:
    - **Performance Colors**: Blue for standard, Orange for 75%+ usage, Red for 90%+.
    - **Floating Design**: A main header bar that blends into the content area.

## Proposed Components
1.  **Dashboard View**: A circular progress gauge showing total RAM % and availability.
2.  **Live Chart**: A scrolling line graph showing usage over the last 60 seconds.
3.  **App Grid**: Cards for each tracked application (Gemini, VS Code, Brave) with their own mini-sparklines.
4.  **Style Customizer**: A sidebar or popover to adjust:
    - **Transparency Level**: (0% to 100%).
    - **Refresh Rate**: (0.5s to 5s).
    - **Color Palette**: Preset themes (Ocean, Forest, Cyberpunk).

## Implementation Strategy (Phase 1)
1.  **Dependencies**: Install `PyGObject` and `libadwaita` introspection libraries.
2.  **Modular Logic**: Keep the existing `MemoryDataCollector` (it's perfect as a backend service).
3.  **UI Loop**: Replace `QTimer` with `GLib.timeout_add` to handle the asynchronous updates in the GTK main loop.
4.  **Blueprint/XML**: Define the UI structure using GtkBuilder XML for better separation of layout and logic.

## Verification
- Validate consistent rendering on both Wayland and X11.
- Test "Adaptive" resizing (window becomes a mobile-style list when narrow).
