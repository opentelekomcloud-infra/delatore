"""Library for monitoring CSM scripts"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


def setup_logger(logger: logging.Logger, log_name: str = None,
                 log_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                 log_dir='./logs'):
    """Setup logger with ``INFO`` level stream output + ``DEBUG`` level rotating file log

    :param logger: logger to be wrapped. Do not wrap same logger twice!
    :param log_name: name of logfile to be created
    :param log_format: format of log output
    :param log_dir: path to rotating file log directory
    """
    formatter = logging.Formatter(log_format)
    if log_name is None:
        log_name = logger.name.lower()
    try:
        # debug+ messages goes to log file
        os.makedirs(log_dir, exist_ok=True)
        f_hdl = TimedRotatingFileHandler(f'{log_dir}/{log_name}.log', encoding='utf-8', backupCount=10, when='midnight',
                                         utc=True)
        f_hdl.setLevel(logging.DEBUG)
        f_hdl.setFormatter(formatter)
        logger.addHandler(f_hdl)
    except OSError:
        pass
    # info+ messages goes to stream
    s_hdl = logging.StreamHandler()
    s_hdl.setLevel(logging.INFO)
    s_hdl.setFormatter(formatter)
    logger.addHandler(s_hdl)


setup_logger(LOGGER, 'delatore', log_dir=os.path.expanduser('~/.delatore/log'))
