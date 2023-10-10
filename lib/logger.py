import logging
import os
import sys
import time
import colorlog

class CustomLogger:
    def __init__(self, log_folder='log'):
        self.log_folder = log_folder

    def create_logger(self):
        # Ensure the log folder exists
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)

        timestamp = time.localtime()
        formatted_timestamp = time.strftime("%Y-%m-%d-%H%M%S", timestamp)
        logname = "".join(["Log", "_", formatted_timestamp, ".log"])
        log_file = os.path.join(self.log_folder, logname)

        # Create a logger instance with colorlog
        logger = colorlog.getLogger()
        logger.setLevel(logging.DEBUG)

        # Create a StreamHandler to log messages to the console with colored output
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        # Create a formatter for console output with colors
        console_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(message)s",
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        )
        console_handler.setFormatter(console_formatter)

        # Create a FileHandler to log messages to the log file
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s.%(msecs)d - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)

        # Add the handlers to the logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

# Example usage in your main script:
if __name__ == "__main__":
    logger_instance = CustomLogger(log_folder="your_custom_log_folder").create_logger()
    logger_instance.debug("This is a debug message.")
    logger_instance.info("This is an info message.")
    logger_instance.warning("This is a warning message.")
    logger_instance.error("This is an error message.")
    logger_instance.critical("This is a critical message.")
