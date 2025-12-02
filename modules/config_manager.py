import configparser
import os
from .constants import Constants

class ConfigManager:
    def __init__(self):
        self.path = Constants.CONFIG_FILE
        self.parser = configparser.ConfigParser()
        self.load()

    def load(self):
        """Reads the config file from disk."""
        self.parser.read(self.path)

    def save(self):
        """Writes the current state to disk."""
        try:
            with open(self.path, 'w') as f:
                self.parser.write(f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_str(self, section, key, fallback=""):
        return self.parser.get(section, key, fallback=fallback)

    def get_int(self, section, key, fallback=0):
        return self.parser.getint(section, key, fallback=fallback)

    def get_float(self, section, key, fallback=0.0):
        return self.parser.getfloat(section, key, fallback=fallback)

    def get_bool(self, section, key, fallback=False):
        return self.parser.getboolean(section, key, fallback=fallback)

    def set(self, section, key, value):
        if not self.parser.has_section(section):
            self.parser.add_section(section)
        self.parser.set(section, key, str(value))