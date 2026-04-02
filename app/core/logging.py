import logging
from logging.config import dictConfig

from pythonjsonlogger import jsonlogger


def configure_logging(log_level: str = 'INFO') -> None:
    dictConfig(
        {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'json': {
                    '()': jsonlogger.JsonFormatter,
                    'fmt': '%(asctime)s %(levelname)s %(name)s %(message)s',
                }
            },
            'handlers': {
                'default': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'json',
                    'level': log_level,
                }
            },
            'root': {'handlers': ['default'], 'level': log_level},
        }
    )
    logging.getLogger(__name__).info('Logging configured', extra={'log_level': log_level})
