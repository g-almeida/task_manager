import time
import subprocess
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RestartHandler(FileSystemEventHandler):
    def __init__(self, command):
        self.command = command
        self.process = None
        self.restart()

    def restart(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        
        # Using a new process group to ensure cleanup on termination
        self.process = subprocess.Popen(self.command)

    def on_modified(self, event):
        if event.src_path.endswith("ram_monitor.py"):
            print(f"\n[Watcher] {event.src_path} changed. Restarting...")
            self.restart()

def main():
    command = [sys.executable, "ram_monitor.py"]
    event_handler = RestartHandler(command)
    observer = Observer()
    observer.schedule(event_handler, path=".", recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
    observer.join()

if __name__ == "__main__":
    main()
