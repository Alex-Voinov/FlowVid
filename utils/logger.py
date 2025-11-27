import logging
import os
from datetime import datetime
from traceback import format_exc


LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def log(message: str, level: str = "info"):
    logger = logging.getLogger("flowvid")
    lvl = level.lower()
    if lvl == "error":
        # Если message пустой — просто логируем traceback
        if not message:
            logger.error(format_exc())
        else:
            logger.error(f"{message}\n{format_exc()}")
    elif lvl == "warning":
        logger.warning(message)
    elif lvl == "debug":
        logger.debug(message)
    elif lvl == "critical":
        logger.critical(message)
    else:
        logger.info(message)
