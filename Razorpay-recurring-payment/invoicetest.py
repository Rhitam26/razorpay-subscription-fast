import asyncio
from datetime import datetime, timedelta
import logging
from sqlalchemy import create_engine, cast, Date
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from models import SubscriptionDueDate, Subscription, Customer
import httpx
from fastapi import HTTPException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection setup
DATABASE_URL = "mssql+pyodbc://:@./razorpaydbnew?driver=ODBC+Driver+17+for+SQL+Server"
engine = create_engine(DATABASE_URL)
try:
    with engine.connect() as connection:
        logger.info("Connected to the database successfully.")
except Exception as e:
    logger.error(f"Error connecting to the database: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Razorpay API credentials and URL
RAZORPAY_API_KEY = "rzp_test_L2TrS6egloWDYm"
RAZORPAY_API_SECRET = "cqaTzYobjoTT8PzgiItV7BGv"
BASE_URL = "https://api.razorpay.com/v1"

# # Fetch the latest invoice for a subscription from Razorpay
# async def fetch_latest_invoice(subscription_id: str):
#     try:
#         logger.info(f"Initiating request to fetch invoices for subscription_id: {subscription_id}")
#         async with httpx.AsyncClient(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET)) as client:
#             response = await client.get(f"{BASE_URL}/invoices?subscription_id={subscription_id}")

#             if response.status_code != 200:
#                 logger.error(f"Error fetching invoices: {response.text}")
#                 raise HTTPException(status_code=response.status_code, detail="Error fetching invoices")
            
#             data = response.json()
#             invoices = data.get("items", [])

#             if not invoices:
#                 logger.info("No invoices found for the subscription.")
#                 return None  # No invoice found, meaning the user hasn't paid yet.

#             # If invoices exist, return the latest one.
#             latest_invoice = max(invoices, key=lambda x: x.get("date", 0))

#             return latest_invoice

#     except Exception as e:
#         logger.error(f"Error in fetching latest invoice: {e}")
#         raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    

# Fetch the latest invoice for a subscription from Razorpay
async def fetch_latest_invoice(subscription_id: str):
    try:
        logger.info(f"Initiating request to fetch invoices for subscription_id: {subscription_id}")
        
        # Make an asynchronous request to Razorpay's invoices API for the given subscription
        async with httpx.AsyncClient(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET)) as client:
            response = await client.get(f"{BASE_URL}/invoices?subscription_id={subscription_id}")

            # Handle failed response from the Razorpay API
            if response.status_code != 200:
                logger.error(f"Error fetching invoices: {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Error fetching invoices")
            
            # Parse the JSON response from Razorpay
            data = response.json()
            invoices = data.get("items", [])

            # If no invoices are found, return a message indicating the invoice is not generated yet
            if not invoices:
                logger.info("No invoices found for the subscription.")
                return {"message": "Invoice not generated yet. Please contact customer care."}

            # Find the latest invoice based on the 'date' field
            latest_invoice = max(invoices, key=lambda x: x.get("date", 0))

            # Extract required details from the latest invoice
            latest_invoice_details = {
                "invoice_number": latest_invoice.get("invoice_number"),
                "email": latest_invoice.get("customer_details", {}).get("email"),
                "contact": latest_invoice.get("customer_details", {}).get("contact"),
                "amount": latest_invoice.get("amount"),
                "unit_amount": latest_invoice.get("line_items", [{}])[0].get("unit_amount"),
                "gross_amount": latest_invoice.get("gross_amount"),
                "net_amount": latest_invoice.get("net_amount"),
                "amount_due": latest_invoice.get("amount_due"),
                "currency": latest_invoice.get("currency"),
                "payment_id": latest_invoice.get("payment_id"),
                "status": latest_invoice.get("status"),
                "issued_at": latest_invoice.get("issued_at"),
                "paid_at": latest_invoice.get("paid_at"),
                "date": latest_invoice.get("date"),
                "billing_start": latest_invoice.get("billing_start"),
                "billing_end": latest_invoice.get("billing_end"),
            }

            logger.info(f"Latest invoice details extracted: {latest_invoice_details}")
            return latest_invoice_details

    except Exception as e:
        logger.error(f"Error in fetching latest invoice: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")



# Check if invoice is generated or not for today's and yesterday's subscriptions
async def check_invoice_generated_or_not_for_today(session: Session):
    """Check invoices for subscriptions with due date today or yesterday."""
    try:
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        logger.info(f"Target dates: Today: {today}, Yesterday: {yesterday}")

        # Fetch subscriptions with today's due date or yesterday's due date
        upcoming_subscriptions = (
            session.query(
                SubscriptionDueDate,
                Customer
            )
            .join(
                Subscription,
                SubscriptionDueDate.subscription_id == Subscription.subscription_id
            )
            .join(
                Customer,
                Subscription.customer_id == Customer.customer_id
            )
            .filter(
                cast(SubscriptionDueDate.due_date, Date).in_([today, yesterday])
            )
            .all()
        )

        if not upcoming_subscriptions:
            logger.info("No upcoming subscriptions found for the target date.")
            return []

        reminder_list = []

        # Iterate through each due subscription
        for due_date, customer in upcoming_subscriptions:
            logger.info(f"Checking invoice for subscription {due_date.subscription_id} due on {due_date.due_date}")

            # Fetch the latest invoice for this subscription from Razorpay
            invoice_details = await fetch_latest_invoice(due_date.subscription_id)
            
            # Log the due date from DB and Razorpay response
            logger.info(f"DB Due Date: {due_date.due_date}, Razorpay Invoice Date: {invoice_details.get('date') if invoice_details else 'No invoice'}")

            # If no invoice is found, mark it as "Payment is due"
            if invoice_details is None:
                # Check if the due date has passed (either today or yesterday)
                if due_date.due_date < today:
                    reminder_list.append({
                        "subscription_id": due_date.subscription_id,
                        "status": "Due date passed, please pay",
                        "message": "Invoice not generated yet. Please contact customer care."
                    })
                else:
                    reminder_list.append({
                        "subscription_id": due_date.subscription_id,
                        "status": "Payment is due",
                        "message": "Invoice not generated yet. Please contact customer care."
                    })
            else:
                # If invoice exists, treat it as paid
                reminder_list.append({
                    "subscription_id": due_date.subscription_id,
                    "status": "Paid",
                    "invoice_details": invoice_details
                })
        
        return reminder_list
    
    except Exception as e:
        logger.error(f"Error in fetching invoice or subscription data: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Main function to execute the logic
async def main():
    session = SessionLocal()
    try:
        # Call the check_invoice_generated_or_not_for_today function
        reminders = await check_invoice_generated_or_not_for_today(session)
        
        if reminders:
            for reminder in reminders:
                if reminder['status'] == "Paid":
                    logger.info(f"Subscription {reminder['subscription_id']} is paid. Invoice Details: {reminder['invoice_details']}")
                else:
                    logger.info(f"Subscription {reminder['subscription_id']} status: {reminder['status']}. Message: {reminder['message']}")
        else:
            logger.info("No subscriptions with pending payments or invoices found.")
    
    except Exception as e:
        logger.error(f"Error occurred: {e}")
    finally:
        session.close()
        logger.info("Database session closed.")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
