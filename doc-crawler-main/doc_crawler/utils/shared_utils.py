import os
import re
import logging
from datetime import datetime
from urllib.parse import urlsplit


def get_logger(timestamp, script_name):
    """
    Sets up a file and console logger.
    Returns the logging module and log file path.
    """
    day = datetime.now().strftime("%d%m%Y")
    log_dir = os.path.join("logs", day)
    os.makedirs(log_dir, exist_ok=True)

    log_filename = f"{timestamp}_{script_name}.log"
    log_path = os.path.join(log_dir, log_filename)

    # Configure root logger (file + console)
    logging.basicConfig(
        filename=log_path,
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

    # # Avoid adding multiple handlers
    # if not any(isinstance(h, logging.StreamHandler) for h in logging.getLogger().handlers):
    #     logging.getLogger().addHandler(console_handler)

    return logging, log_path


def sanitize_filename(url):
    """
    Cleans and formats the filename from a URL for safe saving.
    """
    base = os.path.basename(urlsplit(url).path)
    return re.sub(r"[^\w\-.]", "_", base).replace(" ", "_")
