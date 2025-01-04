from vimmo.logger.logging_config import logger
import sqlite3
from sqlite3 import Connection
from typing import Optional
import importlib.resources
import os
import sys




class Database:
    def __init__(self, db_path: str = 'db/panels_data.db'):
        self.db_path = db_path
        self.conn: Optional[Connection] = None

    def get_db_path(self) -> str:
        """
        Get the database path, handling both development and installed scenarios.
        """
        try:
            # First try to get the database from the installed package
            logger.info("Attempting to get the database in the installed package")
            with importlib.resources.path('vimmo.db', 'panels_data.db') as db_path:
                if not  os.path.isfile(db_path):
                    logger.warning("failed to get the database in the installed package")
                    raise FileNotFoundError("database file could not be located from resource lib")
                logger.info("Database is in the installed package: %s", db_path)
                return str(db_path)
        except Exception:

            # If that fails, try the development path
            logger.info("Attempting to get the database in the development path")
            current_dir = os.path.dirname(os.path.abspath(__file__))
            dev_db_path = os.path.join(current_dir, self.db_path)
            
            if os.path.isfile(dev_db_path):
                logger.info("Database is in the development path at %s", dev_db_path)
                return dev_db_path
            else:
                logger.error("Database file could not be located in either the package or development path")
                raise FileNotFoundError("database file could not be located. Please close the app and create db")
            


    def connect(self):
        """Establish a connection to the SQLite database."""
        if not self.conn:
            try:
                db_path = self.get_db_path()
            except Exception as err:
                logger.critical("database file could not be located. Please close the app and create db")
                raise FileNotFoundError("database file could not be located. Please close the app and create db")
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
            
            
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
        