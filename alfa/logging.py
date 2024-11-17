import logging
from dynaconf import settings

# Map log level to logging module levels
log_level_mapping = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Configure logging
logging.basicConfig(
    level=log_level_mapping[settings.LOG_LEVEL],
    format="%(asctime)s - %(levelname)s - %(message)s",
)

log = logging
