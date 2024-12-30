import httpx
from fastapi import HTTPException
import logging
from datetime import datetime
from models import PlanInput, Customer, Subscription
from utility import convert_to_unix_timestamp
from datetime import datetime, timedelta

# Razorpay API credentials
RAZORPAY_API_KEY = "rzp_test_L2TrS6egloWDYm"
RAZORPAY_API_SECRET = "cqaTzYobjoTT8PzgiItV7BGv"
BASE_URL = "https://api.razorpay.com/v1"

# Configure logging
logger = logging.getLogger(__name__)

class RazorpayService:
    # @staticmethod
    # async def create_or_fetch_customer(session, customer_data: PlanInput, subscription_id=None, plan_id=None, amount_per_recurrence=None):
    #     try:
    #         logger.info("Checking if customer exists in the database...")
    #         existing_customer = (
    #             session.query(Customer)
    #             .filter(
    #                 (Customer.email == customer_data.email)
    #                 | (Customer.phone_number == customer_data.phone_number)
    #             )
    #             .first()
    #         )

    #         if existing_customer:
    #             logger.info(f"Existing customer found: {existing_customer.customer_id}")
    #             if subscription_id and plan_id:
    #                 logger.info("Updating customer with subscription details.")
    #                 existing_customer.subscription_id = subscription_id
    #                 existing_customer.plan_id = plan_id
    #                 existing_customer.amount_per_recurrence = customer_data.amount
    #                 existing_customer.total_recurrence = customer_data.total_count  # Update total_recurrence
    #                 session.commit()  # Update the customer record
    #                 logger.info("Customer updated with subscription details.")
    #             return existing_customer.customer_id

    #         # Customer not found, create on Razorpay
    #         logger.info("Customer not found, creating customer on Razorpay...")
    #         customer_payload = {
    #             "name": customer_data.full_name,
    #             "email": customer_data.email,
    #             "contact": customer_data.phone_number,
    #         }

    #         async with httpx.AsyncClient(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET)) as client:
    #             response = await client.post(f"{BASE_URL}/customers", json=customer_payload)
    #             if response.status_code != 200:
    #                 logger.error(f"Error creating customer on Razorpay: {response.text}")
    #                 raise HTTPException(status_code=response.status_code, detail=response.json())
    #             customer_response = response.json()
    #             customer_id = customer_response.get("id")

    #         logger.info(f"Razorpay customer created: {customer_id}")

    #         # Save the new customer in DB
    #         new_customer = Customer(
    #             customer_id=customer_id,
    #             full_name=customer_data.full_name,
    #             email=customer_data.email,
    #             phone_number=customer_data.phone_number,
    #             subscription_id=subscription_id,
    #             plan_id=plan_id,
    #             amount_per_recurrence=customer_data.amount,
    #             total_recurrence=customer_data.total_count  # Add total_count to the database
    #         )
    #         logger.info(f"Saving new customer to the database: {new_customer}")
    #         session.add(new_customer)
    #         session.commit()
    #         logger.info(f"Customer saved to database: {customer_id}")

    #         return customer_id
    #     except Exception as e:
    #         logger.error(f"Error in create_or_fetch_customer: {e}")
    #         raise

    @staticmethod
    async def create_or_fetch_customer(session, customer_data: PlanInput, subscription_id=None, plan_id=None, amount_per_recurrence=None):
        try:
            logger.info("Checking if customer exists in the database...")
            existing_customer = (
                session.query(Customer)
                .filter(
                    (Customer.email == customer_data.email)
                    | (Customer.phone_number == customer_data.phone_number)
                )
                .first()
            )

            if existing_customer:
                logger.info(f"Existing customer found: {existing_customer.customer_id}")
                if subscription_id and plan_id:
                    logger.info("Updating customer with subscription details.")
                    existing_customer.subscription_id = subscription_id
                    existing_customer.plan_id = plan_id
                    existing_customer.amount_per_recurrence = customer_data.amount
                    existing_customer.total_recurrence = customer_data.total_count
                    session.commit()
                    logger.info(f"Updated customer in database: {existing_customer}")
                return existing_customer.customer_id

            # Customer not found, create on Razorpay
            logger.info("Customer not found, creating customer on Razorpay...")
            customer_payload = {
                "name": customer_data.full_name,
                "email": customer_data.email,
                "contact": customer_data.phone_number,
            }

            async with httpx.AsyncClient(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET)) as client:
                response = await client.post(f"{BASE_URL}/customers", json=customer_payload)
                if response.status_code != 200:
                    logger.error(f"Error creating customer on Razorpay: {response.text}")
                    raise HTTPException(status_code=response.status_code, detail=response.json())
                customer_response = response.json()
                customer_id = customer_response.get("id")

            logger.info(f"Razorpay customer created: {customer_id}")

            # Save the new customer in DB
            logger.info(f"Saving new customer with Amount: {customer_data.amount}, Total Count: {customer_data.total_count}")
            new_customer = Customer(
                customer_id=customer_id,
                full_name=customer_data.full_name,
                email=customer_data.email,
                phone_number=customer_data.phone_number,
                subscription_id=subscription_id,
                plan_id=plan_id,
                amount_per_recurrence=customer_data.amount,
                total_recurrence=customer_data.total_count
            )
            session.add(new_customer)
            session.commit()
            logger.info(f"Customer saved to database: {customer_id}")

            return customer_id
        except Exception as e:
            logger.error(f"Error in create_or_fetch_customer: {e}")
            session.rollback()
            raise


    @staticmethod
    async def create_plan_on_razorpay(plan_input: PlanInput):
        try:
            logger.info("Creating plan on Razorpay...")
            plan_payload = {
                "period": plan_input.period,
                "interval": plan_input.interval,  # Use the user-provided interval
                "item": {
                    "name": f"Plan for {plan_input.full_name}",
                    "amount": plan_input.amount,
                    "currency": plan_input.currency,
                    "description": plan_input.description,
                }
            }

            async with httpx.AsyncClient(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET)) as client:
                logger.info(f"Razorpay Plan Request Body: {plan_payload}")
                response = await client.post(f"{BASE_URL}/plans", json=plan_payload)
                if response.status_code != 200:
                    logger.error(f"Error creating plan on Razorpay: {response.text}")
                    raise HTTPException(status_code=response.status_code, detail=response.json())
                plan_response = response.json()
                plan_id = plan_response.get("id")

            logger.info(f"Plan created successfully: {plan_id}")
            return plan_id
        except Exception as e:
            logger.error(f"Error in create_plan_on_razorpay: {e}")
            raise

    @staticmethod
    async def create_subscription_on_razorpay(plan_input: PlanInput, plan_id: str):
        try:
            logger.info("Creating subscription on Razorpay...")
            subscription_payload = {
                "plan_id": plan_id,
                "total_count": plan_input.total_count,
                "quantity": 1,
                "start_at": convert_to_unix_timestamp(plan_input.start_at),
                "expire_by": convert_to_unix_timestamp(plan_input.expire_by),
                "customer_notify": 1,
                "notes": plan_input.notes,
                "notify_info": {
                    "notify_phone": plan_input.phone_number,
                    "notify_email": plan_input.email,
                }
            }

            async with httpx.AsyncClient(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET)) as client:
                logger.info(f"Razorpay Subscription Request Body: {subscription_payload}")
                response = await client.post(f"{BASE_URL}/subscriptions", json=subscription_payload)
                if response.status_code != 200:
                    logger.error(f"Error creating subscription on Razorpay: {response.text}")
                    raise HTTPException(status_code=response.status_code, detail=response.json())
                subscription_response = response.json()
                subscription_id = subscription_response.get("id")

            logger.info(f"Subscription created successfully: {subscription_id}")
            return subscription_id
        except Exception as e:
            logger.error(f"Error in create_subscription_on_razorpay: {e}")
            raise

    @staticmethod
    async def save_subscription_to_db(session, plan_input: PlanInput, customer_id: str, plan_id: str, subscription_id: str):
        try:
            subscription = Subscription(
                subscription_id=subscription_id,
                customer_id=customer_id,
                plan_id=plan_id,
                start_date=datetime.fromtimestamp(convert_to_unix_timestamp(plan_input.start_at)).date(),
                end_date=datetime.fromtimestamp(convert_to_unix_timestamp(plan_input.expire_by)).date(),
                status="Active",
                created_at=datetime.now()
            )
            session.add(subscription)
            session.commit()
            logger.info(f"Subscription saved to database: {subscription_id}")
        except Exception as e:
            logger.error(f"Error saving subscription to DB: {e}")
            raise


    @staticmethod
    async def fetch_customer_last_updated_by_email(session, email: str):
        try:
            logger.info(f"Fetching last_updated for email: {email}")
            
            # Perform a join query to fetch last_updated directly
            last_updated = (
                session.query(Subscription.last_updated)
                .join(Customer, Customer.customer_id == Subscription.customer_id)
                .filter(Customer.email == email)
                .order_by(Subscription.last_updated.desc())
                .scalar()  # Directly fetch the scalar value
            )
            logger.info(f"------------------------{last_updated}")
            if not last_updated:
                logger.error(f"No subscription found for email: {email}")
                raise HTTPException(status_code=404, detail="No subscription found for the given email")
            
            logger.info(f"Fetched last_updated: {last_updated} for email: {email}")
            logger.info(f"Last updated type: {type(last_updated)}")  # Check the type of last_updated

            # Check if last_updated is more than 30 days ago
            if isinstance(last_updated, datetime):
                days_difference = (datetime.now() - last_updated).days
                logger.info(f"Day Diffrence------------{days_difference }-------------")
                if days_difference > 30:
                    logger.info(f"Yes, last_updated is more than 30 days ago ({days_difference} days).")

                else:
                    logger.info(f"No, last_updated is within the last 30 days ({days_difference} days).")
            
            return str(last_updated)
        except Exception as e:
            logger.error(f"Error in fetch_customer_last_updated_by_email: {e}")
            raise


    @staticmethod
    async def update_customer_data_based_on_subscription(session, subscription_id: str):
        try:
            logger.info(f"Fetching subscription details for ID: {subscription_id} from Subscription table")

            # Fetch subscription data from Subscription table
            subscription = (
                session.query(Subscription)
                .filter(Subscription.subscription_id == subscription_id)
                .first()
            )

            if not subscription:
                logger.error(f"No subscription found in the database for ID: {subscription_id}")
                raise HTTPException(status_code=404, detail="No subscription found in the database.")

            customer_id = subscription.customer_id
            if not customer_id:
                logger.error(f"Subscription {subscription_id} has no associated customer ID.")
                raise HTTPException(status_code=404, detail="No customer ID associated with this subscription.")

            logger.info(f"Fetching customer data for ID: {customer_id} from Customer table")

            # Fetch customer data using customer_id
            customer = (
                session.query(Customer)
                .filter(Customer.customer_id == customer_id)
                .first()
            )

            if not customer:
                logger.error(f"No customer found in the database for ID: {customer_id}")
                raise HTTPException(status_code=404, detail="No customer found in the database.")

            # Call Razorpay API to fetch subscription details
            async with httpx.AsyncClient(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET)) as client:
                logger.info(f"Shuja : {BASE_URL}/subscriptions/{subscription_id}")
                response = await client.get(f"{BASE_URL}/subscriptions/{subscription_id}")
                if response.status_code != 200:
                    logger.error(f"Error fetching subscription from Razorpay: {response.text}")
                    raise HTTPException(status_code=response.status_code, detail=response.json())
                subscription_data = response.json()

            # Extract necessary fields from API response
            api_total_count = subscription_data.get("total_count")
            api_remaining_count = subscription_data.get("remaining_count")
            api_current_recurrence = api_total_count - api_remaining_count if api_total_count and api_remaining_count else None

            # Compare and update fields if necessary
            updates = {}
            if customer.total_recurrence != api_total_count:
                updates["total_recurrence"] = api_total_count
            if customer.current_recurrence != api_current_recurrence:
                updates["current_recurrence"] = api_current_recurrence

            if updates:
                # Add update timestamp
                updates["updated_on"] = datetime.utcnow()
                for key, value in updates.items():
                    setattr(customer, key, value)
                session.commit()
                logger.info(f"Customer data updated in database: {updates}")
                return updates

            logger.info("No updates required. Database matches Razorpay API.")
            return {"message": "No updates required."}
        except Exception as e:
            logger.error(f"Error in update_customer_data_based_on_subscription: {e}")
            raise
