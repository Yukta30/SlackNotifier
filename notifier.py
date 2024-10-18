import os
import yaml
import requests
import psutil  # for CPU monitoring
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

# Load configuration
with open("config.yaml", 'r') as config_file:
    config = yaml.safe_load(config_file)

SLACK_WEBHOOK_URL = config['slack_webhook_url']
MONITOR_DIR = config['monitor_directory']
ALERT_KEYWORDS = config['alert_on_keywords']
CPU_THRESHOLD = config['cpu_threshold']

# Slack notifier function
def send_slack_notification(message: str):
    payload = {"text": message}
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    if response.status_code != 200:
        print(f"Failed to send notification. Status code: {response.status_code}, Response: {response.text}")

# Event handler for file changes
class LogFileEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(".log"):
            print(f"Log file changed: {event.src_path}")
            self.process_log(event.src_path)

    def process_log(self, log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()

        # Check the last few lines for errors or warnings
        for line in lines[-10:]:  # last 10 lines
            if any(keyword in line for keyword in ALERT_KEYWORDS):
                send_slack_notification(f"Alert: {line.strip()}")

# Monitor CPU usage
def monitor_cpu_usage():
    cpu_usage = psutil.cpu_percent(interval=1)
    if cpu_usage > CPU_THRESHOLD:
        send_slack_notification(f"High CPU usage detected: {cpu_usage}%")

# Main function to start monitoring
def main():
    event_handler = LogFileEventHandler()
    observer = Observer()
    observer.schedule(event_handler, MONITOR_DIR, recursive=False)

    print(f"Monitoring directory: {MONITOR_DIR}")
    observer.start()

    try:
        while True:
            monitor_cpu_usage()  # Check CPU usage periodically
            time.sleep(10)       # Sleep for 10 seconds between checks
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == "__main__":
    main()
