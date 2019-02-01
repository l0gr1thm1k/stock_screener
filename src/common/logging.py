import logging
import structlog
import uuid
from logging import config as logging_config

LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR
}


def get_new_request_id():
    """
    gets a new UUID string for a request

    :return: UUID string
    """

    return str(uuid.uuid4()).replace('-', '')


def log_exception(ex=None, message='Unhandled exception', **kwargs):
    """
    log an exception with a traceback

    :param ex: Exception
    :param message: optional message
    :param kwargs: additional fields for log entry
    """

    logger = structlog.get_logger()
    logger.exception(event=message, exceptionType=type(ex).__name__, exceptionMessage=str(ex), exc_info=True, **kwargs)


def setup_logging(level='info'):
    """
    setup Structlog logging

    :param level: log level
    """
    logging_config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                'format': '%(message)s %(process)d %(thread)d %(pathname)s %(lineno)d',
                'class': 'pythonjsonlogger.jsonlogger.JsonFormatter'
            }
        },
        'handlers': {
            'json': {
                'class': 'logging.StreamHandler',
                'formatter': 'json'
            }
        },
        'loggers': {
            '': {
                'handlers': ['json'],
                'level': LOG_LEVELS[level.lower()]
            }
        }
    })
    structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                structlog.processors.format_exc_info,
                structlog.processors.StackInfoRenderer(),
                structlog.stdlib.render_to_log_kwargs
            ],
            context_class=structlog.threadlocal.wrap_dict(dict),
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True
    )

    logging.getLogger('pbcommon').setLevel(logging.WARNING)
    logging.getLogger('flask').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('connexion').setLevel(logging.WARNING)
    logging.getLogger('swagger_spec_validator').setLevel(logging.WARNING)
    logging.getLogger('openapi_spec_validator').setLevel(logging.WARNING)
    logging.getLogger('boto').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('s3transfer').setLevel(logging.WARNING)
    logging.getLogger('numpy').setLevel(logging.WARNING)
    logging.getLogger('scipy').setLevel(logging.WARNING)
    logging.getLogger('sklearn').setLevel(logging.WARNING)
    logging.getLogger('keras').setLevel(logging.WARNING)
    logging.getLogger('tensorflow').setLevel(logging.WARNING)
    logging.getLogger('gensim').setLevel(logging.ERROR)
    logging.getLogger('nltk').setLevel(logging.WARNING)
    logging.getLogger('spacy').setLevel(logging.WARNING)
