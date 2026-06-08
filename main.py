import sys
import gi
import time
import collections
import os
import psutil
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gio, Pango, Gdk

# --- Data Logic ---

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
                usage_mb = info['memory_info'].rss / (1024 * 1024)
                if usage_mb < 0.1:
                    continue

                tty = info['terminal']
                if tty and 'pts/' in tty:
                    if tty not in terminal_usage:
                        terminal_usage[tty] = {'usage': 0.0, 'apps': []}
                    terminal_usage[tty]['usage'] += usage_mb
                    if info['name'] not in ['bash', 'zsh', 'sh', 'fish', 'gnome-terminal-']:
                        terminal_usage[tty]['apps'].append(info['name'])
                    continue

                cmdline = " ".join(info['cmdline']) if info['cmdline'] else ""
                matched_tracked = False
                for label, pattern in self.tracked_patterns.items():
                    if pattern in cmdline or pattern in info['name']:
                        tracked_usage[label] += usage_mb
                        matched_tracked = True
                        break
                
                if matched_tracked:
                    continue

                name = info['name']
                other_usage[name] = other_usage.get(name, 0.0) + usage_mb

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return self._format_and_sort_results(tracked_usage, terminal_usage, other_usage, system_total_mb)

    def _format_and_sort_results(self, tracked: dict, terminals: dict, others: dict, total_mb: int) -> List[AppUsage]:
        results = []
        for label, usage in tracked.items():
            if usage > 0.1:
                results.append(AppUsage(label, usage, (usage / total_mb * 100)))
        for tty, data in terminals.items():
            active_apps = [a for a in data['apps'] if a]
            app_label = active_apps[-1] if active_apps else "Idle"
            label = f"Terminal ({tty.split('/')[-1]}) [{app_label}]"
            results.append(AppUsage(label, data['usage'], (data['usage'] / total_mb * 100)))
        sorted_others = sorted(others.items(), key=lambda x: x[1], reverse=True)
        for name, usage in sorted_others[:3]:
            results.append(AppUsage(f"[Top] {name}", usage, (usage / total_mb * 100)))
        results.sort(key=lambda x: x.usage_mb, reverse=True)
        return results

# --- GUI Logic ---

CSS = """
.glass-box {
    background-color: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.status-title {
    font-size: 32pt;
    font-weight: bold;
}

.chart-area {
    background-color: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    margin: 12px;
}
"""

class RAMMonitorApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id='com.gabriel.rammonitor',
                         flags=Gio.ApplicationFlags.FLAGS_NONE,
                         **kwargs)
        self.collector = MemoryDataCollector({
            'Gemini': '/bin/gemini',
            'VSCode': '/usr/share/code/code',
            'Brave': '/opt/brave.com/brave/brave'
        })

    def do_activate(self):
        # Load CSS
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        self.win = RAMMonitorWindow(application=self, collector=self.collector)
        self.win.present()

class RAMMonitorWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        self.collector = kwargs.pop('collector')
        super().__init__(*args, **kwargs)
        
        self.set_title("RAM Monitor")
        self.set_default_size(480, 700)
        self.history = collections.deque([0] * 60, maxlen=60)
        self.is_transparent = False
        
        self.setup_ui()
        
        GLib.timeout_add_seconds(1, self.update_stats)
        self.update_stats()

    def setup_ui(self):
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.main_box)
        
        self.header = Adw.HeaderBar()
        self.main_box.append(self.header)
        
        self.btn_t = Gtk.Button(label="T")
        self.btn_t.set_tooltip_text("Toggle Transparency")
        self.btn_t.connect("clicked", self.toggle_transparency)
        self.header.pack_end(self.btn_t)
        
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_vexpand(True)
        self.main_box.append(self.scroll)
        
        self.clamp = Adw.Clamp()
        self.scroll.set_child(self.clamp)
        
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.content_box.set_margin_all(18)
        self.clamp.set_child(self.content_box)
        
        self.hero_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.hero_box.add_css_class("glass-box")
        self.hero_box.set_margin_bottom(12)
        
        self.lbl_hero_percent = Gtk.Label(label="0.0%")
        self.lbl_hero_percent.add_css_class("status-title")
        self.hero_box.append(self.lbl_hero_percent)
        
        self.lbl_hero_desc = Gtk.Label(label="Initializing...")
        self.lbl_hero_desc.add_css_class("caption")
        self.hero_box.append(self.lbl_hero_desc)
        
        self.content_box.append(self.hero_box)
        
        chart_group = Adw.PreferencesGroup(title="Usage History (60s)")
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_content_height(100)
        self.drawing_area.set_draw_func(self.draw_chart)
        self.drawing_area.add_css_class("chart-area")
        chart_group.add(self.drawing_area)
        self.content_box.append(chart_group)
        
        self.apps_group = Adw.PreferencesGroup(title="Process Insights")
        self.content_box.append(self.apps_group)

    def toggle_transparency(self, button):
        self.is_transparent = not self.is_transparent
        if self.is_transparent:
            self.set_opacity(0.7)
            button.add_css_class("suggested-action")
        else:
            self.set_opacity(1.0)
            button.remove_css_class("suggested-action")

    def draw_chart(self, area, cr, width, height):
        if not self.history:
            return
        cr.set_line_width(2)
        cr.set_source_rgba(0.35, 0.65, 1.0, 0.8)
        step = width / (len(self.history) - 1)
        for i, val in enumerate(self.history):
            x = i * step
            y = height - (val / 100.0 * height)
            if i == 0:
                cr.move_to(x, y)
            else:
                cr.line_to(x, y)
        cr.stroke_preserve()
        cr.line_to(width, height)
        cr.line_to(0, height)
        cr.close_path()
        cr.set_source_rgba(0.35, 0.65, 1.0, 0.2)
        cr.fill()

    def update_stats(self):
        stats = self.collector.get_system_stats()
        if not stats:
            return True
        self.history.append(stats.percent)
        self.lbl_hero_percent.set_label(f"{stats.percent:.1f}%")
        self.lbl_hero_desc.set_label(f"{stats.used} MB used of {stats.total} MB")
        self.drawing_area.queue_draw()
        app_usage = self.collector.collect_all_usage(stats.total)
        child = self.apps_group.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            if isinstance(child, Adw.ActionRow):
                self.apps_group.remove(child)
            child = next_child
        for app in app_usage:
            row = Adw.ActionRow(title=app.label)
            row.set_subtitle(f"{app.percent_of_total:.1f}% of total")
            bar = Gtk.ProgressBar()
            bar.set_fraction(app.percent_of_total / 100.0)
            bar.set_valign(Gtk.Align.CENTER)
            bar.set_size_request(80, -1)
            lbl = Gtk.Label(label=f"{app.usage_mb:.0f} MB")
            lbl.set_margin_start(12)
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            box.append(bar)
            box.append(lbl)
            row.add_suffix(box)
            self.apps_group.add(row)
        return True

def main():
    app = RAMMonitorApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    main()
