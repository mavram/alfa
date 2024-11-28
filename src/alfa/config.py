import logging

from dynaconf import Dynaconf

settings = Dynaconf(
    environments=True,
    settings_files=["settings.toml", ".secrets.toml"],
    envvar_prefix="ALFA",
)

# Map log level to logging module levels
log_level_mapping = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
logging_level = log_level_mapping[settings.LOG_LEVEL]

# Configure Application logging
logging.basicConfig(
    level=logging_level,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Configure ORM logging
logging.getLogger("peewee").setLevel(logging_level)

log = logging
