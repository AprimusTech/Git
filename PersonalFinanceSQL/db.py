import configparser
from pathlib import Path
import pyodbc



class Database:
    def __init__(self):
        self.config_path = Path(__file__).with_name('config.ini')
        self.connection_string = ''
        if self.config_path.exists():
            cfg = configparser.ConfigParser()
            cfg.read(self.config_path)
            self.connection_string = cfg.get('sqlserver', 'connection_string', fallback='').strip()

    def connect(self):
        if not self.connection_string:
            raise RuntimeError('SQL Server connection is not configured. Create config.ini using config.ini.example.')
        return pyodbc.connect(self.connection_string, timeout=5)


