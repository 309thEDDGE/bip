import logging
import os
from datetime import datetime


def create_logger(
    module_name,
    parser_name,
    logger_level=logging.DEBUG,
    log_dir=os.path.join(os.getcwd(), "bip", "logs")
):
    if not (os.path.exists(log_dir)):
        os.makedirs(log_dir)

    local_filename = f"bip_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.log"
    local_file = os.path.join(log_dir, local_filename)
    file_handler = logging.FileHandler(local_file)
    logger = logging.getLogger(module_name)
    fmt = logging.Formatter(
        fmt="%(parser_name)s - %(asctime)s [%(levelname)s]: %(message)s")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    logger.setLevel(logger_level)

    extra = {"parser_name": parser_name}
    logger = logging.LoggerAdapter(logger, extra)

    return logger
