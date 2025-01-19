from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
import logging

# Configure logging in the database module as well
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.info("************************************************")


DATABASE_URL = "mssql+pyodbc://:@./razorpaydbnew?driver=ODBC+Driver+17+for+SQL+Server"
engine = create_engine(DATABASE_URL)
try:
    # Attempt to connect to the database
    with engine.connect() as connection:
        logger.info("Connected to the database successfully.")
except Exception as e:
    logger.error(f"Error connecting to the database: {e}")

# SQLAlchemy session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy base model
Base = declarative_base()