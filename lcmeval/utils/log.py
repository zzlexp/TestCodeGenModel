"""Central logging configuration shared across lcmeval modules."""

import logging
import numpy as np
from logging import Logger as Logger

__all__ = ['setup_logger', 'Logger']


def setup_logger(log_file='run.log'):
    """
    Set up a logger with two handlers: one for console output and one for file output.
    Args:
        log_file (str): The path to the log file.
    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger(log_file)
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    np.set_printoptions(threshold=np.inf)

    formatter = logging.Formatter('%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
