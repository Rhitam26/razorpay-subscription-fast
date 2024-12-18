
from fastapi import FastAPI, HTTPException
import logging
from razorpay_services import RazorpayService
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
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@app.post("/create-subscription/", response_model=FinalResponse)
async def create_subscription(db: db_dependency, plan_input: PlanInput):
    try:
        logger.info(f"Plan API Request Body: {plan_input.model_dump_json()}")

        customer_id = await RazorpayService.create_or_fetch_customer(db, plan_input)
        plan_id = await RazorpayService.create_plan_on_razorpay(plan_input)
        subscription_id = await RazorpayService.create_subscription_on_razorpay(plan_input, plan_id)
        await RazorpayService.save_subscription_to_db(db, plan_input, customer_id, plan_id, subscription_id)

        logger.info(f"Subscription created successfully: subscription_id={subscription_id}, customer_id={customer_id}")
        return FinalResponse(
            subscription_id=subscription_id,
            customer_id=customer_id,
            message="Subscription created successfully!"
        )
    except HTTPException as e:
        logger.error(f"HTTPException occurred: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()
