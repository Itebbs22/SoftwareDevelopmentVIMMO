# Importing the logging modules and handlers

import logging
from logging.handlers import RotatingFileHandler
import os
# from vimmo.logger.logging_config import console_handler, file_handler
LOG_DIR = os.path.dirname(os.path.realpath(__file__))
# print(f"Log DIR: {LOG_DIR}")
LOG_FILE = os.path.join(LOG_DIR,"vimmo.log")
# print(f"Log FILE: {LOG_FILE}")



# Logger creation

logger = logging.getLogger("VIMMO")
logger.setLevel(logging.DEBUG) # making the default logger at DEBUG level to log all messages

# Defining the formatters

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Handler creation for dual destination logging

# Setting up the console handler for logging to the terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.CRITICAL) # Logs INFO level and  above to the console
console_handler.setFormatter(formatter)

# Setting up the file handler for logging to a file with rotation
file_handler = RotatingFileHandler(os.path.join(LOG_DIR, LOG_FILE), maxBytes=5 * 1024 * 1024, backupCount=3) # This rotates the logs when the file size exceeds 10 MB
file_handler.setLevel(logging.INFO) # Logs DEBUG level and above to the file
file_handler.setFormatter(formatter)

# Adding handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
