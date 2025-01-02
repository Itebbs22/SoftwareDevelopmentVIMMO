import logging
import logging.handlers
from typing import Optional, Dict, Any, List
import sqlite3
from sqlite3 import Error

class CustomLogger:
    def __init__(self):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)  # Set the default logging level to DEBUG

        self.formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def _setup_console_handler(self) -> logging.Handler:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.console_logging_level)
        console_handler.setFormatter(self.formatter)
        return console_handler
    
    def log(self, level: int, message: str, handlers: List[str]):
        temp_logger = logging.getLogger(f"{self.logger.name}")
        temp_logger.setLevel(logging.DEBUG)

        # Log the message
        temp_logger.log(level, message)

        # Remove handlers after logging
        temp_logger.handlers.clear()

    def debug(self, message: str, handlers: List[str] = ["console"]):
        self.log(logging.DEBUG, message, handlers)

    def info(self, message: str, handlers: List[str] = ["console"]):
        self.log(logging.INFO, message, handlers)

    def warning(self, message: str, handlers: List[str] = ["console"]):
        self.log(logging.WARNING, message, handlers)

    def error(self, message: str, handlers: List[str] = ["console"]):
        self.log(logging.ERROR, message, handlers)

    def critical(
        self, message: str, handlers: List[str] = ["console"]
    ):
        self.log(logging.CRITICAL, message, handlers)


class LoggingDatabase:
    def __init__(self, db_file) -> None:
        """Initialize the database connection."""
        self.db_file = db_file
        self.conn = None
        self.create_connection()
        self.create_schema()
        self.close_connection()

    def create_connection(self) -> None:
        """Create a database connection to the database."""
        try:
            self.conn = sqlite3.connect(self.db_file)
            logger.debug(f"Connected to the database: {self.db_file}")
        except Error as e:
            logger.info(f"Error connecting to database: {e}")

    def close_connection(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.debug("Database connection closed.")
