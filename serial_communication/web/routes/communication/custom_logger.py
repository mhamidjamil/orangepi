"""default logging functionality of python"""
import logging

# Configure the logging module
logging.basicConfig(filename='logger.txt', level=logging.INFO)

def log_message(level, msg):
    """Log a message with the specified log level."""
    if level == 'info':
        logging.info(msg)
    elif level == 'warning':
        logging.warning(msg)
    elif level == 'error':
        logging.error(msg)
    else:
        raise ValueError(f"Invalid log level: {level}")

# def add_info(msg):
#     log_message('info', msg)

# def add_warning(msg):
#     log_message('warning', msg)

# def add_error(msg):
#     log_message('error', msg)
