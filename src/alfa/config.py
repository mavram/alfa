import logging

from dynaconf import Dynaconf, Validator

# Load and validate settings
settings = Dynaconf(
    environments=True,
    settings_files=["settings.toml", ".secrets.toml"],
    envvar_prefix="ALFA",
)

# settings.validators.register(
#     # Global settings validators
#     Validator("global.portfolio_name", must_exist=True, is_type_of=str),
#     # Environment-specific validators
#     Validator("dev.log_level", must_exist=True, is_in=["DEBUG", "INFO", "WARNING", "ERROR"]),
#     Validator("dev.db_path", must_exist=True, is_type_of=str),
#     Validator("testing.log_level", must_exist=True, is_in=["DEBUG", "INFO", "WARNING", "ERROR"]),
#     Validator("testing.db_path", must_exist=True, is_type_of=str),
#     Validator("prod.log_level", must_exist=True, is_in=["DEBUG", "INFO", "WARNING", "ERROR"]),
#     Validator("prod.db_path", must_exist=True, is_type_of=str),
# )
# settings.validators.validate(only_current_env=True)

# Map log level to logging module levels
log_level_mapping = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
logging_level = log_level_mapping[settings.LOG_LEVEL]

# Configure application logging
logging.basicConfig(
    level=logging_level,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Configure ORM logging
logging.getLogger("peewee").setLevel(logging_level)

log = logging
