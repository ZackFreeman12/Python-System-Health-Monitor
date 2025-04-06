# Python System Health Monitor

![Python Version](https://img.shields.io/badge/python-3.6%2B-blue.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A desktop application built with Python and Tkinter to monitor key system health metrics in real-time, featuring threshold-based alerts via GUI, sound, and email.

![Screenshot Placeholder](<path_to_your_screenshot.png>)
*(Optional: Replace the line above with an actual screenshot of your application!)*

## Overview

This application provides a simple graphical user interface (GUI) to monitor various system performance indicators on your machine. It helps users keep an eye on resource usage and network status, triggering alerts when predefined thresholds are exceeded.

## Features

*   **Real-time Monitoring:** Tracks crucial system metrics automatically.
*   **GUI Display:** Presents information clearly using Tkinter.
*   **Metrics Monitored:**
    *   CPU Usage (%)
    *   Memory Usage (%)
    *   Disk Usage (%) for all physical partitions
    *   Network Latency (Ping to 8.8.8.8 by default)
    *   Network I/O (Bytes Sent/Received per second)
    *   Disk I/O (Bytes Read/Written per second)
    *   System Uptime
*   **Threshold Alerts:**
    *   Highlights metrics in red on the GUI when thresholds are breached.
    *   Plays an audible beep sound (Windows only via `winsound`).
    *   Sends email notifications for critical alerts.
*   **Configurable Email Alerts:** Set up SMTP server details, sender/recipient emails, and credentials through a dedicated settings window. Configuration is saved locally (`config/email_settings.json`).
*   **Report Saving:** Generate and save a snapshot of the current system health metrics to a text file (`reports/`).
*   **Automatic Refresh:** Metrics are updated automatically every few seconds.

## Requirements

*   Python 3.6+
*   External Libraries:
    *   `psutil`: For accessing system details (CPU, memory, disk, network, uptime).
    *   `ping3`: For network latency measurement (may require administrator/root privileges on some systems).
*   Standard Libraries: `tkinter` (usually included with Python), `json`, `os`, `smtplib`, `datetime`, `time`, `logging`.
*   `winsound` (for beep alerts - Windows only, optional).

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <repository-directory>
    ```
2.  **Install required libraries:**
    ```bash
    pip install psutil ping3
    # or use pip install -r requirements.txt if you create one
    ```
    *Note: `ping3` might require running the script with elevated privileges (e.g., using `sudo` on Linux/macOS or "Run as administrator" on Windows) for ICMP pings to work reliably.*

## Usage

1.  Navigate to the directory containing the script.
2.  Run the application:
    ```bash
    python your_main_script_name.py
    ```
    (Replace `your_main_script_name.py` with the actual name of your Python file).

## Configuration

*   **Email Alerts:**
    *   Click the "Email Settings" button in the application.
    *   Fill in your SMTP server details (e.g., `smtp.gmail.com`), port (e.g., `587` for TLS), sender email address, sender password (use an App Password if using Gmail/services with 2FA), and the recipient email address.
    *   Click "Save". The settings will be stored in `config/email_settings.json`.
    *   Ensure your sender email account allows sign-in from less secure apps OR preferably use an "App Password" if available (recommended for Gmail, Outlook, etc.).
*   **Thresholds:**
    *   Currently, thresholds are hardcoded within the `SystemHealthGUI` class `__init__` method. Modify these values directly in the script if needed.

## Future Enhancements

*   Allow configuration of thresholds via the GUI or a separate config file.
*   Add historical data logging and graphical charts (e.g., using Matplotlib).
*   Make the ping target configurable.
*   Implement cross-platform sound alerts.
*   Package the application into an executable (e.g., using PyInstaller).
*   More robust error handling and logging.
*   Monitor specific processes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or open an Issue.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details (or add the MIT license text directly).