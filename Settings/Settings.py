import json


class WdSettings:
    settings = None
    logging = None

    def __init__(self, logging):
        self.logging = logging
        self.load_settings()

    def load_settings(self):
        try:
            with open('settings.json', 'r') as file:
                self.settings = json.load(file)
            self.logging.add_log("Settings file loaded")
        except FileNotFoundError:
            self.logging.add_log("Settings file not found, using default settings")
            self.settings = {
                "name": "default",
                "app": "",
                "arguments": [],
                "ports": [8000, 8005],
                "ping_time": 30,
                "wait": 60,
                "reboot": 4,
                "autostart": False
            }
            self.save_settings()

    def save_settings(self):
        with open('settings.json', 'w') as file:
            json.dump(self.settings, file, indent=4)

    def get_settings(self):
        return self.settings
