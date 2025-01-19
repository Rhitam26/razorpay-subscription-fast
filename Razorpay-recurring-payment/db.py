from database import SessionLocal
import logging
# Configure logging
logging.basicConfig(
    filename="application.log",  # Log file
    level=logging.INFO,          # Logging level
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Error during database session: {e}")
    finally:
        db.close()