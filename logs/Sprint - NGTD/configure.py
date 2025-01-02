import logging

# Logging Configuration

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)

# Logger creation
logger = logging.getLogger("VIMMO")

# Using the logger to log messages
logger.debug("This is a debug message")

