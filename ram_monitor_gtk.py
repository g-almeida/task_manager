import sys
import gi
import time
import collections

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib, Gio, Pango, Gdk
from ram_monitor import MemoryDataCollector

# Custom CSS for Glassmorphism and Styling
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
        
        # Load CSS
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS, -1)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def do_activate(self):
        self.win = RAMMonitorWindow(application=self, collector=self.collector)
        self.win.present()

class RAMMonitorWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        self.collector = kwargs.pop('collector')
        super().__init__(*args, **kwargs)
        
        self.set_title("RAM Monitor")
        self.set_default_size(480, 700)
        self.history = collections.deque([0] * 60, maxlen=60) # 60 seconds of history
        self.is_transparent = False
        
        self.setup_ui()
        
        # Update Loop
        GLib.timeout_add_seconds(1, self.update_stats)
        self.update_stats()

    def setup_ui(self):
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.main_box)
        
        # Header Bar
        self.header = Adw.HeaderBar()
        self.main_box.append(self.header)
        
        # Transparency Toggle Button
        self.btn_t = Gtk.Button(label="T")
        self.btn_t.set_tooltip_text("Toggle Transparency")
        self.btn_t.connect("clicked", self.toggle_transparency)
        self.header.pack_end(self.btn_t)
        
        # Content
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_vexpand(True)
        self.main_box.append(self.scroll)
        
        self.clamp = Adw.Clamp()
        self.scroll.set_child(self.clamp)
        
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.content_box.set_margin_all(18)
        self.clamp.set_child(self.content_box)
        
        # 1. Dashboard View (Hero Stat)
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
        
        # 2. Live Pulse Chart (DrawingArea)
        chart_group = Adw.PreferencesGroup(title="Usage History (60s)")
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_content_height(100)
        self.drawing_area.set_draw_func(self.draw_chart)
        self.drawing_area.add_css_class("chart-area")
        chart_group.add(self.drawing_area)
        self.content_box.append(chart_group)
        
        # 3. App Grid
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
        # Background
        cr.set_source_rgba(0, 0, 0, 0) # Transparent background (handled by CSS)
        cr.paint()
        
        if not self.history:
            return
            
        # Line setup
        cr.set_line_width(2)
        cr.set_source_rgba(0.35, 0.65, 1.0, 0.8) # Light blue
        
        step = width / (len(self.history) - 1)
        
        # Draw path
        for i, val in enumerate(self.history):
            x = i * step
            # Scale val (0-100) to height (inverted y)
            y = height - (val / 100.0 * height)
            if i == 0:
                cr.move_to(x, y)
            else:
                cr.line_to(x, y)
                
        cr.stroke_preserve()
        
        # Fill area under line
        cr.line_to(width, height)
        cr.line_to(0, height)
        cr.close_path()
        cr.set_source_rgba(0.35, 0.65, 1.0, 0.2)
        cr.fill()

    def update_stats(self):
        stats = self.collector.get_system_stats()
        if not stats:
            return True
            
        # Update Data
        self.history.append(stats.percent)
        
        # Update Hero
        self.lbl_hero_percent.set_label(f"{stats.percent:.1f}%")
        self.lbl_hero_desc.set_label(f"{stats.used} MB used of {stats.total} MB")
        
        # Redraw Chart
        self.drawing_area.queue_draw()
        
        # Update App List
        app_usage = self.collector.collect_all_usage(stats.total)
        
        # Sync rows
        child = self.apps_group.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            if isinstance(child, Adw.ActionRow):
                self.apps_group.remove(child)
            child = next_child
            
        for app in app_usage:
            row = Adw.ActionRow(title=app.label)
            row.set_subtitle(f"{app.percent_of_total:.1f}% of total")
            
            # Progress Bar for each app
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

if __name__ == "__main__":
    app = RAMMonitorApp()
    app.run(sys.argv)
