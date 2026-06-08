import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QLabel, QGroupBox, QTreeWidget, QTreeWidgetItem, QWidget)
from PySide6.QtCore import QTimer, Qt
from ram_monitor import MemoryDataCollector, MemoryStats, AppUsage

class RAMMonitorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time RAM Monitor (Linux)")
        self.resize(600, 500)
        
        # Tracked Apps
        self.tracked_apps = {
            'Gemini': '/bin/gemini',
            'VSCode': '/usr/share/code/code',
            'Brave': '/opt/brave.com/brave/brave'
        }
        
        self.collector = MemoryDataCollector(self.tracked_apps)
        
        self.setup_ui()
        
        # Setup Timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000) # 1 second
        
        self.update_data()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # System Stats Group
        stats_group = QGroupBox("System Statistics")
        stats_layout = QHBoxLayout()
        
        self.lbl_total = QLabel("Total: -- MB")
        self.lbl_used = QLabel("Used: -- MB")
        self.lbl_available = QLabel("Available: -- MB")
        self.lbl_percent = QLabel("Usage: -- %")
        
        stats_layout.addWidget(self.lbl_total)
        stats_layout.addWidget(self.lbl_used)
        stats_layout.addWidget(self.lbl_available)
        stats_layout.addWidget(self.lbl_percent)
        stats_group.setLayout(stats_layout)
        
        main_layout.addWidget(stats_group)
        
        # Application Usage Group
        app_group = QGroupBox("Application Usage (Sorted)")
        app_layout = QVBoxLayout()
        
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Application", "Usage (MB)", "% of Total"])
        self.tree.setColumnWidth(0, 250)
        
        app_layout.addWidget(self.tree)
        app_group.setLayout(app_layout)
        
        main_layout.addWidget(app_group)

    def update_data(self):
        system_stats = self.collector.get_system_stats()
        if system_stats:
            self.lbl_total.setText(f"Total: {system_stats.total} MB")
            self.lbl_used.setText(f"Used: {system_stats.used} MB")
            self.lbl_available.setText(f"Available: {system_stats.available} MB")
            self.lbl_percent.setText(f"Usage: {system_stats.percent:.1f}%")
            
            app_usage = self.collector.collect_all_usage(system_stats.total)
            
            # Update Tree
            self.tree.clear()
            for app in app_usage:
                item = QTreeWidgetItem([
                    app.label,
                    f"{app.usage_mb:.1f}",
                    f"{app.percent_of_total:.1f}%"
                ])
                # Align numbers to the right
                item.setTextAlignment(1, Qt.AlignRight)
                item.setTextAlignment(2, Qt.AlignRight)
                self.tree.addTopLevelItem(item)

def main():
    app = QApplication(sys.argv)
    window = RAMMonitorGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
