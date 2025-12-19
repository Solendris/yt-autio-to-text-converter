import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger():
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_filename = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')

    logger = logging.getLogger('app_logger')
    logger.setLevel(logging.DEBUG)

    log_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_handler = RotatingFileHandler(
        log_filename,
        maxBytes=5*1024*1024,
        backupCount=3
    )
    file_handler.setFormatter(log_formatter)
    
    # Avoid adding multiple handlers if setup is called multiple times
    if not logger.handlers:
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(log_formatter)
        logger.addHandler(console_handler)

    return logger

logger = setup_logger()
