from datetime import datetime
import logging

logging.basicConfig(
    filename="application.log",  # Log file
    level=logging.INFO,          # Logging level
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
# Utility function
def convert_to_unix_timestamp(date_str: str) -> int:
    dt = datetime.strptime(date_str, "%d-%m-%Y")
    logger.info(f"Converted to UNIX {int(dt.timestamp())}")
    return int(dt.timestamp())