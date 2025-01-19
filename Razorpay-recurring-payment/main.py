
from fastapi import FastAPI, HTTPException
import logging
from razorpay_services import RazorpayService, SubscriptionNotificationService
from models import PlanInput, FinalResponse
from db import get_db
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session


# FastAPI initialization
app = FastAPI()
db_dependency = Annotated[Session, Depends(get_db)]

# Configure logging
logging.basicConfig(
    filename="application.log",
    level=logging.DEBUG,  # Set to DEBUG for detailed logs
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@app.post("/create-subscription/", response_model=FinalResponse)
async def create_subscription(db: db_dependency, plan_input: PlanInput):
    try:
        logger.info(f"Received request to create subscription with plan input: {plan_input.model_dump_json()}")

        # Step 1: Validate interval for daily plans
        if plan_input.period == "daily" and plan_input.interval < 7:
            logger.error(f"Invalid interval value: {plan_input.interval}. For daily plans, interval must be at least 7 days.")
            raise HTTPException(status_code=400, detail="For daily plans, interval must be at least 7 days.")
        
        # Step 2: Create or fetch customer from Razorpay
        logger.debug("Creating or fetching customer from Razorpay...")
        customer_id = await RazorpayService.create_or_fetch_customer(db, plan_input)
        logger.debug(f"Customer fetched or created: customer_id={customer_id}")

        # Step 3: Create plan on Razorpay
        logger.debug("Creating plan on Razorpay...")
        plan_id = await RazorpayService.create_plan_on_razorpay(plan_input)
        logger.debug(f"Plan created: plan_id={plan_id}")

        # Step 4: Create subscription on Razorpay
        logger.debug("Creating subscription on Razorpay...")
        subscription_id = await RazorpayService.create_subscription_on_razorpay(plan_input, plan_id)
        logger.debug(f"Subscription created: subscription_id={subscription_id}")

        # Step 5: Save subscription to the database
        logger.debug("Saving subscription to the database...")
        await RazorpayService.save_subscription_to_db(db, plan_input, customer_id, plan_id, subscription_id)
        logger.info(f"Subscription saved to database successfully: subscription_id={subscription_id}")

        # Step 6: Generate due dates
        logger.info("Generating due dates...")
        due_dates = RazorpayService.generate_due_dates(subscription_id, plan_input.amount, plan_input.start_at,
                                           plan_input.total_count, plan_input.period, plan_input.expire_by, plan_input.interval)
        logger.info(f"Generated due dates: {due_dates}")
        print(f"***************** {type(due_dates)}")    
        
        # Step 7: Save due dates to the database
        await RazorpayService.save_due_dates_to_db(db, subscription_id, due_dates)
        logger.info(f"Due dates saved to the database.")

        # Log each due date for better traceability
        for due_date in due_dates:
            logger.info(f"Generated due date: {due_date}")

        logger.info(f"Subscription creation successful: subscription_id={subscription_id}, customer_id={customer_id}")
        return FinalResponse(
            subscription_id=subscription_id,
            customer_id=customer_id,
            message="Subscription created successfully!",
             due_dates=due_dates 
        )

    except HTTPException as e:
        logger.error(f"HTTPException occurred: {e.detail}")
        # FastAPI will automatically return the correct response for HTTPException
        raise e

    except Exception as e:
        logger.error(f"Unexpected error occurred while creating subscription: {str(e)}")
        # Raise internal server error in case of any unexpected error
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    finally:
        db.close()
        logger.debug("Database session closed.")

@app.get("/customer-last-updated/")
async def fetch_last_updated(email: str, db: db_dependency):
    try:
        logger.info(f"Fetching last updated info for customer with email: {email}")
        last_updated = await RazorpayService.fetch_customer_last_updated_by_email(db, email)
        logger.debug(f"Fetched last updated info: {last_updated}")
        return {
            "last_updated": last_updated,
            "Message": "Customer last updated fetched successfully!"
        }
    except HTTPException as e:
        logger.error(f"HTTPException occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching last updated info for email {email}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()
        logger.debug("Database session closed.")


@app.get("/update-customer-data/")
async def update_customer_data(subscription_id: str, db: db_dependency):
    try:
        logger.info(f"Updating customer data for subscription_id: {subscription_id}")
        result = await RazorpayService.update_customer_data_based_on_subscription(db, subscription_id)
        logger.debug(f"Customer data updated successfully: {result}")
        return {
            "updated_data": result,
            "Message": "Customer data fetched and updated successfully!"
        }
    except HTTPException as e:
        logger.error(f"HTTPException occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error occurred while updating customer data for subscription_id {subscription_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()
        logger.debug("Database session closed.")


@app.get("/latest-invoice/")
async def fetch_latest_invoice(subscription_id: str):
    try:
        logger.info(f"Fetching latest invoice for subscription_id: {subscription_id}")
        latest_invoice_details = await RazorpayService.fetch_latest_invoice(subscription_id)
        logger.debug(f"Fetched latest invoice details: {latest_invoice_details}")
        return {
            "message": "Latest invoice fetched successfully!",
            "data": latest_invoice_details
        }
    except HTTPException as e:
        logger.error(f"HTTPException occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching latest invoice for subscription_id {subscription_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/subscription-invoice-status/")
async def check_subscription_invoice_status(db: db_dependency):
    try:
        logger.info("Checking if invoice has been generated for the subscription.")
        latest_invoice_details = await SubscriptionNotificationService.check_invoice_generated_or_not_for_today(db)

        if "message" in latest_invoice_details:
            logger.info("Invoice has not been generated yet.")
            return {
                "message": "Invoice not generated yet. Please contact customer care.",
                "status": "Not Generated"
            }

        logger.info("Invoice fetched successfully.")
        return {
            "message": "Invoice fetched successfully!",
            "data": latest_invoice_details
        }

    except HTTPException as e:
        logger.error(f"HTTPException occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error occurred while checking invoice status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/overdue-subscriptions-status-7Days/")
async def check_overdue_subscriptions_status(db: db_dependency):
    try:
        logger.info("Checking overdue subscriptions that are 7+ days overdue and invoice not generated.")
        overdue_subscription_details = await SubscriptionNotificationService.check_overdue_subscriptions(db)

        if not overdue_subscription_details:
            logger.info("No overdue subscriptions found.")
            return {
                "message": "No overdue subscriptions found.",
                "status": "No overdue"
            }

        logger.info("Overdue subscriptions checked successfully.")
        return {
            "message": "Overdue subscriptions checked successfully!",
            "data": overdue_subscription_details
        }

    except HTTPException as e:
        logger.error(f"HTTPException occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error occurred while checking overdue subscriptions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def lambda_handler(event, context):
    return app(event, context)