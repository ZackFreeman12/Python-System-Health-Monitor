import tkinter as tk
from tkinter import ttk, messagebox
import winsound 
import psutil
import ping3
from datetime import datetime
import json
import os
import smtplib
from email.message import EmailMessage
import logging
import time 

# --- EmailSettingsWindow class remains the same ---
class EmailSettingsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Email Settings")
        self.geometry("400x300")
        self.parent = parent
        self.settings_file = "config/email_settings.json"
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)

        # Load existing settings
        self.settings = self.load_settings()

        # Create GUI elements
        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self, text="SMTP Server:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.smtp_server = ttk.Entry(self, width=30) # Increased width
        self.smtp_server.grid(row=0, column=1, padx=5, pady=5)
        self.smtp_server.insert(0, self.settings.get("smtp_server", ""))

        ttk.Label(self, text="SMTP Port:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.smtp_port = ttk.Entry(self, width=10) # Set specific width
        self.smtp_port.grid(row=1, column=1, padx=5, pady=5, sticky="w") # Align left
        self.smtp_port.insert(0, self.settings.get("smtp_port", "587"))  # Default TLS port

        ttk.Label(self, text="Sender Email:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.sender_email = ttk.Entry(self, width=30) # Increased width
        self.sender_email.grid(row=2, column=1, padx=5, pady=5)
        self.sender_email.insert(0, self.settings.get("sender_email", ""))

        ttk.Label(self, text="Password:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.password = ttk.Entry(self, show="*", width=30) # Increased width
        self.password.grid(row=3, column=1, padx=5, pady=5)
        self.password.insert(0, self.settings.get("password", ""))

        ttk.Label(self, text="Recipient Email:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.recipient_email = ttk.Entry(self, width=30) # Increased width
        self.recipient_email.grid(row=4, column=1, padx=5, pady=5)
        self.recipient_email.insert(0, self.settings.get("recipient_email", ""))

        save_button = ttk.Button(self, text="Save", command=self.save_settings)
        save_button.grid(row=5, column=1, pady=10, sticky="e") # Align right

    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                messagebox.showwarning("Load Settings", f"Could not read settings file '{self.settings_file}'. It might be corrupted. Using defaults.")
                return {}
            except Exception as e:
                messagebox.showerror("Load Settings", f"Error loading settings: {e}")
                return {}
        return {}

    def save_settings(self):
        # Basic validation
        if not all([self.smtp_server.get(), self.smtp_port.get(), self.sender_email.get(), self.recipient_email.get()]):
             messagebox.showwarning("Save Settings", "Please fill in all fields (Password is optional if not needed by your provider).")
             return
        try:
             port = int(self.smtp_port.get())
             if not (0 < port < 65536):
                 raise ValueError("Port number out of range")
        except ValueError:
            messagebox.showwarning("Save Settings", "Invalid SMTP Port number.")
            return

        self.settings = {
            "smtp_server": self.smtp_server.get(),
            "smtp_port": self.smtp_port.get(),
            "sender_email": self.sender_email.get(),
            "password": self.password.get(), # Store password, consider more secure storage later
            "recipient_email": self.recipient_email.get()
        }
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=4) # Add indent for readability
            messagebox.showinfo("Save Settings", "Settings saved successfully.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Save Settings", f"Error saving settings: {e}")

# --- SystemHealthGUI class ---
class SystemHealthGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("System Health Monitor")
        self.root.geometry("550x550") # Increased size for new metrics

        # --- Thresholds ---
        self.thresholds = {
            "cpu_usage": 80,
            "memory_usage": 90,
            "disk_usage": 90, # Threshold for *any* disk
            "network_latency_ms": 100
        }

        # --- State for calculating rates ---
        self.last_time = time.time()
        self.last_net_io = psutil.net_io_counters()
        self.last_disk_io = psutil.disk_io_counters()

        # --- GUI Setup ---
        self.create_widgets()
        self.update_metrics() # Initial data fetch
        self.schedule_update() # Start automatic refresh

    def create_widgets(self):
        # Main Frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)

        # --- Metrics Frame ---
        metrics_frame = ttk.LabelFrame(main_frame, text="System Metrics", padding="10")
        metrics_frame.pack(fill="x", pady=5)
        metrics_frame.columnconfigure(1, weight=1) # Allow value column to expand

        row_num = 0
        self.labels = {} 

        # CPU
        ttk.Label(metrics_frame, text="CPU Usage:").grid(row=row_num, column=0, sticky="w", pady=2)
        self.labels["cpu"] = ttk.Label(metrics_frame, text="- %")
        self.labels["cpu"].grid(row=row_num, column=1, sticky="w", padx=5)
        row_num += 1

        # Memory
        ttk.Label(metrics_frame, text="Memory Usage:").grid(row=row_num, column=0, sticky="w", pady=2)
        self.labels["memory"] = ttk.Label(metrics_frame, text="- %")
        self.labels["memory"].grid(row=row_num, column=1, sticky="w", padx=5)
        row_num += 1

        # Uptime
        ttk.Label(metrics_frame, text="System Uptime:").grid(row=row_num, column=0, sticky="w", pady=2)
        self.labels["uptime"] = ttk.Label(metrics_frame, text="-")
        self.labels["uptime"].grid(row=row_num, column=1, sticky="w", padx=5)
        row_num += 1

        # --- Disk Usage Section ---
        self.disk_frame = ttk.Frame(metrics_frame) # Frame to hold dynamic disk labels
        self.disk_frame.grid(row=row_num, column=0, columnspan=2, sticky="ew", pady=(5,0))
        self.disk_labels = {} # Dict to store labels for each disk: {mountpoint: label_widget}
        row_num += 1 # Increment row for next section

        # Network Latency
        ttk.Label(metrics_frame, text="Network Latency:").grid(row=row_num, column=0, sticky="w", pady=2)
        self.labels["network_latency"] = ttk.Label(metrics_frame, text="- ms")
        self.labels["network_latency"].grid(row=row_num, column=1, sticky="w", padx=5)
        row_num += 1

        # Network I/O
        ttk.Label(metrics_frame, text="Network I/O (Sent/Recv):").grid(row=row_num, column=0, sticky="w", pady=2)
        self.labels["network_io"] = ttk.Label(metrics_frame, text="- / - per sec")
        self.labels["network_io"].grid(row=row_num, column=1, sticky="w", padx=5)
        row_num += 1

        # Disk I/O
        ttk.Label(metrics_frame, text="Disk I/O (Read/Write):").grid(row=row_num, column=0, sticky="w", pady=2)
        self.labels["disk_io"] = ttk.Label(metrics_frame, text="- / - per sec")
        self.labels["disk_io"].grid(row=row_num, column=1, sticky="w", padx=5)
        row_num += 1

        # --- Buttons Frame ---
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=10, fill="x", side="bottom") # Place at bottom

        ttk.Button(buttons_frame, text="Refresh Now", command=self.update_metrics).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Save Report", command=self.save_report).pack(side="left", padx=5)
        ttk.Button(buttons_frame, text="Email Settings", command=self.open_email_settings).pack(side="right", padx=5) # Move to right

    def format_bytes(self, B):
        """Return the given bytes as a human friendly KB, MB, GB, or TB string."""
        KB = 1024.0
        MB = KB * 1024.0
        GB = MB * 1024.0
        TB = GB * 1024.0

        if B < KB: return f"{B} B"
        if KB <= B < MB: return f"{B/KB:.2f} KB"
        if MB <= B < GB: return f"{B/MB:.2f} MB"
        if GB <= B < TB: return f"{B/GB:.2f} GB"
        if TB <= B: return f"{B/TB:.2f} TB"

    def format_timedelta(self, td):
        """Formats a timedelta object into a readable string (D days, HH:MM:SS)."""
        total_seconds = int(td.total_seconds())
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days > 0:
            return f"{days}d, {hours:02}:{minutes:02}:{seconds:02}"
        else:
            return f"{hours:02}:{minutes:02}:{seconds:02}"

    def open_email_settings(self):
        # Check if window already exists
        # Basic check: If a window with this title owned by root exists
        for win in self.root.winfo_children():
             if isinstance(win, tk.Toplevel) and win.title() == "Email Settings":
                 win.lift() # Bring to front
                 return
        # If not found, create a new one
        EmailSettingsWindow(self.root)

    def get_system_health(self):
        current_time = time.time()
        time_delta = current_time - self.last_time
        if time_delta == 0: time_delta = 1 # Avoid division by zero on first/fast calls

        data = {"timestamp": datetime.now()}

        # --- Basic Metrics ---
        data["cpu_usage"] = psutil.cpu_percent(interval=None) # Non-blocking
        data["memory_usage"] = psutil.virtual_memory().percent

        # --- Uptime ---
        boot_time_timestamp = psutil.boot_time()
        elapsed_time = datetime.now() - datetime.fromtimestamp(boot_time_timestamp)
        data["uptime"] = elapsed_time

        # --- Disk Usage (All Physical Disks) ---
        data["disk_usages"] = {} # Dictionary to store {mountpoint: percent}
        try:
            partitions = psutil.disk_partitions()
            for p in partitions:
                # Try to filter for physical disks (heuristic)
                # Check 'opts' for 'fixed' or similar if available and needed
                # Check device path format if needed (e.g., ignore '/dev/loop')
                # Simple filter: has a filesystem type and is not a CD/DVD drive (common on Windows)
                if p.fstype and 'cdrom' not in p.opts:
                     try:
                         usage = psutil.disk_usage(p.mountpoint)
                         data["disk_usages"][p.mountpoint] = usage.percent
                     except PermissionError:
                          print(f"Permission error accessing disk {p.mountpoint}")
                     except FileNotFoundError:
                         print(f"Disk {p.mountpoint} not found (maybe ejected?).")
                     except Exception as e:
                         print(f"Error getting disk usage for {p.mountpoint}: {e}")
        except Exception as e:
            print(f"Could not list disk partitions: {e}")


        # --- Network Latency ---
        data["network_latency_ms"] = None
        try:
            # Consider making the target host configurable
            latency = ping3.ping("8.8.8.8", timeout=1) # Reduced timeout
            if latency is not None: # ping3 returns None on timeout/error
                data["network_latency_ms"] = round(latency * 1000, 2)
            else:
                data["network_latency_ms"] = "Timeout/Error"
        except Exception as e:
            # Ping can fail due to permissions (needs raw sockets) or network issues
            print(f"Network ping error: {e}")
            data["network_latency_ms"] = "Error"

        # --- Network I/O Rate ---
        current_net_io = psutil.net_io_counters()
        bytes_sent_per_sec = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_delta
        bytes_recv_per_sec = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_delta
        data["network_io"] = (bytes_sent_per_sec, bytes_recv_per_sec)
        self.last_net_io = current_net_io

        # --- Disk I/O Rate ---
        current_disk_io = psutil.disk_io_counters()
        read_bytes_per_sec = (current_disk_io.read_bytes - self.last_disk_io.read_bytes) / time_delta
        write_bytes_per_sec = (current_disk_io.write_bytes - self.last_disk_io.write_bytes) / time_delta
        data["disk_io"] = (read_bytes_per_sec, write_bytes_per_sec)
        self.last_disk_io = current_disk_io

        # --- Update last time ---
        self.last_time = current_time

        return data

    def send_email_alert(self, alert_message):
        settings_file = "config/email_settings.json"
        if not os.path.exists(settings_file):
            print("Email settings file not found. Skipping email alert.")
            # Optionally show a one-time message box
            # messagebox.showwarning("Email Alert", "Email settings not configured. Cannot send alert.")
            return

        try:
            with open(settings_file, "r") as f:
                settings = json.load(f)

            # Validate required settings
            required = ["smtp_server", "smtp_port", "sender_email", "recipient_email"]
            if not all(settings.get(key) for key in required):
                 print("Email settings incomplete. Skipping email alert.")
                 # Optionally show a message box
                 # messagebox.showwarning("Email Alert", "Email settings are incomplete. Cannot send alert.")
                 return

            msg = EmailMessage()
            msg.set_content(f"System Alert:\n{alert_message}\n\nTimestamp: {datetime.now()}")
            msg["Subject"] = "System Health Monitor Alert"
            msg["From"] = settings["sender_email"]
            msg["To"] = settings["recipient_email"]

            # Connect to SMTP server
            port = int(settings["smtp_port"]) # Convert port to int
            password = settings.get("password") # Get password, might be empty/None

            with smtplib.SMTP(settings["smtp_server"], port) as server:
                server.ehlo() # Identify ourselves to the server
                server.starttls() # Enable encryption (standard practice)
                server.ehlo() # Re-identify ourselves after TLS
                if password: # Only login if password is provided
                     server.login(settings["sender_email"], password)
                server.send_message(msg)

            print("Email alert sent successfully!")

        except FileNotFoundError:
             print(f"Email settings file not found at {settings_file}") # Should be caught earlier, but good practice
        except json.JSONDecodeError:
             messagebox.showerror("Email Error", f"Failed to parse email settings file '{settings_file}'.")
        except smtplib.SMTPAuthenticationError:
             messagebox.showerror("Email Error", "SMTP Authentication Error. Check sender email/password.")
        except smtplib.SMTPConnectError:
             messagebox.showerror("Email Error", f"Could not connect to SMTP server '{settings['smtp_server']}:{port}'.")
        except Exception as e:
            # Catch other potential SMTP errors or general errors
            messagebox.showerror("Email Error", f"Failed to send email alert: {str(e)}")

    def check_thresholds(self, data):
        alerts = []
        alert_details = {} # Store details for the email/message

        # Reset colors first
        self.labels["cpu"].config(foreground="black")
        self.labels["memory"].config(foreground="black")
        for label in self.disk_labels.values():
             label.config(foreground="black")
        self.labels["network_latency"].config(foreground="black")
        # Add resets for I/O if thresholds are added for them

        # Check CPU
        if data["cpu_usage"] > self.thresholds["cpu_usage"]:
            alerts.append("CPU Usage")
            alert_details["CPU Usage"] = f"{data['cpu_usage']:.1f}% (Threshold: {self.thresholds['cpu_usage']}%)"
            self.labels["cpu"].config(foreground="red")

        # Check Memory
        if data["memory_usage"] > self.thresholds["memory_usage"]:
            alerts.append("Memory Usage")
            alert_details["Memory Usage"] = f"{data['memory_usage']:.1f}% (Threshold: {self.thresholds['memory_usage']}%)"
            self.labels["memory"].config(foreground="red")

        # Check Disks
        for mountpoint, usage in data["disk_usages"].items():
            if usage > self.thresholds["disk_usage"]:
                disk_name = f"Disk Usage ({mountpoint})"
                if disk_name not in alerts: # Avoid duplicate 'Disk Usage' entries if multiple disks exceed
                     alerts.append(disk_name)
                alert_details[disk_name] = f"{usage:.1f}% (Threshold: {self.thresholds['disk_usage']}%)"
                if mountpoint in self.disk_labels:
                    self.disk_labels[mountpoint].config(foreground="red")

        # Check Network Latency
        latency = data["network_latency_ms"]
        if isinstance(latency, (int, float)) and latency > self.thresholds["network_latency_ms"]:
            alerts.append("Network Latency")
            alert_details["Network Latency"] = f"{latency} ms (Threshold: {self.thresholds['network_latency_ms']} ms)"
            self.labels["network_latency"].config(foreground="red")

        # --- Trigger Alert Actions ---
        if alerts:
            alert_summary = f"Thresholds exceeded: {', '.join(alerts)}"
            print(f"ALERT: {alert_summary}") # Log to console

            # Prepare detailed message
            detailed_alert_msg = f"The following system metrics exceeded their thresholds:\n\n"
            for key, value in alert_details.items():
                detailed_alert_msg += f"- {key}: {value}\n"

            # Beep Sound (Windows only)
            try:
                 winsound.Beep(1000, 500) # Frequency 1000Hz, Duration 500ms
            except RuntimeError:
                 print("Could not play beep sound (winsound unavailable or error).")
            except ImportError:
                 print("winsound module not available (non-Windows OS?). Skipping beep.")


            # Show Warning Dialog Box
            # Consider making this optional or less frequent to avoid annoyance
            # messagebox.showwarning("System Alert", detailed_alert_msg)

            # Send Email
            self.send_email_alert(detailed_alert_msg)

    def update_metrics(self):
        try:
            health_data = self.get_system_health()

            # --- Update Labels ---
            self.labels["cpu"].config(text=f"{health_data['cpu_usage']:.1f} %")
            self.labels["memory"].config(text=f"{health_data['memory_usage']:.1f} %")
            self.labels["uptime"].config(text=f"{self.format_timedelta(health_data['uptime'])}")

            # Update Disk Usage Labels (Dynamically)
            # Clear previous disk labels first
            for widget in self.disk_frame.winfo_children():
                widget.destroy()
            self.disk_labels.clear()

            disk_row = 0
            if health_data["disk_usages"]:
                 ttk.Label(self.disk_frame, text="Disk Usage:").grid(row=disk_row, column=0, sticky="wn", pady=2) # Add header label
                 #disk_row+=1 # This might push the disk values down too much - keep on same logical row
                 col_num=1 # Start values in column 1
                 max_cols = 2 # How many disk entries per row (label+value)
                 disk_in_row = 0
                 for mountpoint, usage in health_data["disk_usages"].items():
                    # Create label pair for each disk
                    lbl_name = ttk.Label(self.disk_frame, text=f"  {mountpoint}:")
                    lbl_name.grid(row=disk_row, column=col_num, sticky="w", pady=1, padx=(5,0))
                    lbl_value = ttk.Label(self.disk_frame, text=f"{usage:.1f} %")
                    lbl_value.grid(row=disk_row, column=col_num + 1, sticky="w", padx=(0, 15))
                    self.disk_labels[mountpoint] = lbl_value # Store reference to value label for coloring

                    disk_in_row += 1
                    if disk_in_row >= max_cols :
                        disk_row += 1 # Move to next row
                        col_num = 1 # Reset to first value column
                        disk_in_row = 0
                    else:
                        col_num += 2 # Move to next pair in the same row


            else:
                 # If no disks found, display a message
                 ttk.Label(self.disk_frame, text="Disk Usage: Not Available").grid(row=disk_row, column=0, columnspan=2, sticky="w", pady=2)


            # Network Latency
            latency_val = health_data['network_latency_ms']
            if isinstance(latency_val, (int, float)):
                 self.labels["network_latency"].config(text=f"{latency_val} ms")
            else: # Handle "Timeout/Error" or None
                 self.labels["network_latency"].config(text=str(latency_val))


            # Network I/O
            sent_bps, recv_bps = health_data['network_io']
            self.labels["network_io"].config(
                 text=f"{self.format_bytes(sent_bps)}ps / {self.format_bytes(recv_bps)}ps"
             )

            # Disk I/O
            read_bps, write_bps = health_data['disk_io']
            self.labels["disk_io"].config(
                 text=f"{self.format_bytes(read_bps)}ps / {self.format_bytes(write_bps)}ps"
            )

            # --- Check Thresholds ---
            self.check_thresholds(health_data)

        except Exception as e:
            messagebox.showerror("Update Error", f"An error occurred during metric update: {e}")
            # Optionally, stop scheduled updates if the error is persistent or critical
            # self.root.after_cancel(self.update_id)

    def schedule_update(self):
        """Schedules the next update_metrics call."""
        self.update_metrics() # Run now
        # Schedule next run after 30000ms (30 seconds)
        # Make interval configurable if needed
        self.update_id = self.root.after(30000, self.schedule_update)

    def save_report(self):
        # Get fresh data just before saving
        try:
            health_data = self.get_system_health()
            os.makedirs("reports", exist_ok=True) # Ensure directory exists
            filename = f"reports/system_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "w") as f:
                f.write(f"=== System Health Report ===\n")
                f.write(f"Timestamp: {health_data['timestamp']}\n\n")

                f.write(f"CPU Usage: {health_data['cpu_usage']:.1f}%\n")
                f.write(f"Memory Usage: {health_data['memory_usage']:.1f}%\n")
                f.write(f"System Uptime: {self.format_timedelta(health_data['uptime'])}\n\n")

                f.write("Disk Usage:\n")
                if health_data["disk_usages"]:
                    for mp, usage in health_data["disk_usages"].items():
                        f.write(f"  - {mp}: {usage:.1f}%\n")
                else:
                    f.write("  (No disk usage data available)\n")
                f.write("\n")

                latency = health_data['network_latency_ms']
                latency_str = f"{latency} ms" if isinstance(latency, (int, float)) else str(latency)
                f.write(f"Network Latency (to 8.8.8.8): {latency_str}\n")

                net_sent_bps, net_recv_bps = health_data['network_io']
                f.write(f"Network I/O Rate (Sent/Recv): {self.format_bytes(net_sent_bps)}ps / {self.format_bytes(net_recv_bps)}ps\n")

                disk_read_bps, disk_write_bps = health_data['disk_io']
                f.write(f"Disk I/O Rate (Read/Write): {self.format_bytes(disk_read_bps)}ps / {self.format_bytes(disk_write_bps)}ps\n")

            messagebox.showinfo("Success", f"Report saved to {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save report: {str(e)}")
            logging.exception("Failed to save report") # Log detailed error


if __name__ == "__main__":
    # Basic logging setup
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    root = tk.Tk()
    app = SystemHealthGUI(root)

    # Handle window close event to cancel the scheduled update
    def on_closing():
        if hasattr(app, 'update_id'):
             root.after_cancel(app.update_id)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()