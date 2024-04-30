# TDWatchdog

TDWatchdog is a simple Python script that can handle logging and status for the installations.

## Installation
Run "install.bat" to install the required packages.

## Usage
- Run "run.bat" to start the script.
- "settings.json" contains the settings for the application you want to run.
- "TD" folder contains the TouchDesigner component that is used to communicate with the script and example file.
    - You can build your own logic around this component based on the status of your installation. I usually setting up check for sensors and devices or local errors in TD that would communicate with Watchdog component.

