# Expected Behavior
# Lambda receives webhook from Razorpay.
# Parses JSON payload to extract subscription_id and status.
# Updates the database if the subscription_id exists.
# Commits changes and logs the update.
# Handles errors properly and returns appropriate HTTP responses.
import json
import os
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from models import Subscription  # Ensure this is correctly imported

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ************************************************
logger.info("Starting AWS Lambda for Razorpay Webhooks...")
# ************************************************

# Database connection details
DATABASE_URL = "mssql+pyodbc://:@./razorpaydbnew?driver=ODBC+Driver+17+for+SQL+Server"

# Setup SQLAlchemy Engine and Session
engine = create_engine(DATABASE_URL)
try:
    with engine.connect() as connection:
        logger.info("Connected to the database successfully.")
except Exception as e:
    logger.error(f"Error connecting to the database: {e}")

# SQLAlchemy session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy Base Model
Base = declarative_base()


def lambda_handler(event, context):
    """
    AWS Lambda handler function for Razorpay webhooks.
    Updates subscription status in the database.
    """
    # Get the Razorpay Webhook Secret (if needed for validation)
    RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET', '')

    try:
        # Parse JSON body from API Gateway
        body = json.loads(event.get('body', '{}'))  

        # Extract required data
        event_type = body.get('event')
        subscription_data = body.get('payload', {}).get('subscription', {}).get('entity', {})

        subscription_id = subscription_data.get('id')
        customer_id = subscription_data.get('customer_id')  # Might be None
        status = subscription_data.get('status')

        if not subscription_id or not status:
            raise ValueError("Invalid webhook data: Missing subscription_id or status")

        logger.info(f"Received Event: {event_type}, Subscription ID: {subscription_id}, Status: {status}")

        # Update subscription status in the database
        db: Session = SessionLocal()
        try:
            subscription = db.query(Subscription).filter(Subscription.subscription_id == subscription_id).first()

            if subscription:
                subscription.status = status  # Update status from webhook
                subscription.last_updated = datetime.now()
                db.commit()
                logger.info(f"Updated Subscription {subscription_id} to Status: {status}")
            else:
                logger.warning(f"Subscription {subscription_id} not found in DB.")

        except Exception as db_error:
            logger.error(f"Database error while updating subscription {subscription_id}: {db_error}")
            db.rollback()
        finally:
            db.close()

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Webhook processed successfully'})
        }

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }
