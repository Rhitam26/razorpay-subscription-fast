
import dotenv
import httpx
from fastapi import HTTPException
import logging
from datetime import datetime
from models import PlanInput, Customer, Subscription, SubscriptionDueDate
from utility import convert_to_unix_timestamp
from datetime import datetime, timedelta
from sqlalchemy import create_engine, cast, Date
from sqlalchemy.sql.sqltypes import Date
from sqlalchemy import cast as sqlalchemy_cast
import os


dotenv.load_dotenv()

RAZORPAY_API_KEY=os.getenv("API_KEY")
RAZORPAY_API_SECRET = os.getenv("API_SECRET")




# Razorpay API credentials
# RAZORPAY_API_KEY = "rzp_test_L2TrS6egloWDYm"
# RAZORPAY_API_SECRET = "cqaTzYobjoTT8PzgiItV7BGv"
# RAZORPAY_API_KEY = "rzp_test_hTNeHzM03SutGO"
# RAZORPAY_API_SECRET = "ljRGUsfzvsEAT3Rdq4Z7m7my"
BASE_URL = "https://api.razorpay.com/v1"

# Configure logging
logger = logging.getLogger(__name__)

class RazorpayService:

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
            # Step 1: Validate the interval based on the period
            if plan_input.period == "daily" and plan_input.interval < 7:
                logger.error(f"Invalid interval value: {plan_input.interval}. For daily plans, interval must be at least 7 days.")
                raise HTTPException(status_code=400, detail="For daily plans, interval must be at least 7 days.")
            
            logger.info("Creating plan on Razorpay...")
            
            # Step 2: Prepare the payload for the Razorpay plan creation request
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

            # Step 3: Make the request to Razorpay API
            async with httpx.AsyncClient(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET)) as client:
                logger.info(f"Razorpay Plan Request Body: {plan_payload}")
                response = await client.post(f"{BASE_URL}/plans", json=plan_payload)

                # Step 4: Handle response from Razorpay
                if response.status_code != 200:
                    error_message = f"Error creating plan on Razorpay: {response.text}"
                    logger.error(error_message)
                    try:
                        error_details = response.json()
                    except Exception as parse_error:
                        logger.error(f"Error parsing Razorpay error response: {parse_error}")
                        error_details = {"message": "Unable to parse error details"}
                    raise HTTPException(status_code=response.status_code, detail=error_details)

                # Step 5: Extract plan details from the response
                plan_response = response.json()
                plan_id = plan_response.get("id")

                if not plan_id:
                    logger.error("Plan ID not found in the Razorpay response.")
                    raise HTTPException(status_code=500, detail="Plan ID not returned by Razorpay")

            # Step 6: Return the plan ID if successfully created
            logger.info(f"Plan created successfully: {plan_id}")
            return plan_id

        except HTTPException as e:
            # Handle specific HTTP errors
            logger.error(f"HTTPException occurred: {e.detail}")
            raise e
        except Exception as e:
            # Catch all other exceptions and log them
            logger.error(f"Unexpected error in create_plan_on_razorpay: {e}")
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

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
                logger.info(f"*** Subscription Response *** :- {subscription_response}")
                subscription_id = subscription_response.get("id")
                short_url=subscription_response.get("short_url")

            logger.info(f"Subscription created successfully: {subscription_id}")
            return subscription_id , short_url
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
                status="Pending",
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            session.add(subscription)
            session.commit()
            logger.info(f"Subscription saved to database: {subscription_id}")
        except Exception as e:
            logger.error(f"Error saving subscription to DB: {e}")
            raise

    @staticmethod
    def generate_due_dates(subscription_id, amount, start_date, total_count, interval, expire_by, period_duration):
        """
        Generate due dates for a billing plan with the given start date, interval, and expire by.

        Args:
        - subscription_id (str): Unique subscription ID.
        - amount (float): Amount for each billing cycle.
        - start_date (str or datetime): The start date of the first cycle (can be in string or datetime format).
        - total_count (int): Total number of billing cycles.
        - interval (str): Billing interval (e.g., "weekly", "daily", "monthly", "yearly").
        - expire_by (str or datetime): The latest date by which all billing cycles should complete.
        - period_duration (int): The period length for the interval (e.g., 1 for weekly, 7 for days, etc.).

        Returns:
        - List of dictionaries containing due dates and related information.
        """
        # Convert start_date and expire_by to datetime objects if they are in string format
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%d-%m-%Y')  # Convert start date to datetime
        if isinstance(expire_by, str):
            expire_by = datetime.strptime(expire_by, '%d-%m-%Y')  # Convert expire_by to datetime

        # Initialize variables
        due_dates = []
        current_due_date = start_date

        # Generate due dates
        for recurrence in range(1, total_count + 1):
            # Check if the current due date exceeds expire_by
            if current_due_date > expire_by:
                break

            # Calculate the next due date based on the interval and period_duration
            if interval == "daily":
                next_due_date = current_due_date + timedelta(days=period_duration)
            elif interval == "weekly":
                next_due_date = current_due_date + timedelta(weeks=period_duration)
            elif interval == "monthly":
                next_due_date = current_due_date + relativedelta(months=period_duration)
            elif interval == "quarterly":
                next_due_date = current_due_date + relativedelta(months=3 * period_duration)  # Quarterly = 3 months
            elif interval == "yearly":
                next_due_date = current_due_date + relativedelta(years=period_duration)
            else:
                raise ValueError(f"Unsupported interval '{interval}'. Supported intervals: daily, weekly, monthly, quarterly, yearly.")
            
            # Append the due date details
            due_dates.append({
                "subscription_id": subscription_id,
                "amount": amount,
                "due_date": current_due_date.strftime('%d-%m-%Y'),
                "recurrence": recurrence,
                "mail_status": "Pending",
                "duration_from": current_due_date.strftime('%d-%m-%Y'),
                "duration_upto": next_due_date.strftime('%d-%m-%Y') if next_due_date <= expire_by else expire_by.strftime('%d-%m-%Y')
            })

            # Update current_due_date for the next cycle
            current_due_date = next_due_date

        return due_dates

    @staticmethod
    async def save_due_dates_to_db(session, subscription_id: str, due_dates: list):
        """
        Save the generated due dates to the database.

        Args:
        - session: The database session.
        - subscription_id (str): The subscription ID associated with the due dates.
        - due_dates (list): A list of dictionaries containing due dates and related information.
        """
        try:
            for due_date in due_dates:
                subscription_due_date = SubscriptionDueDate(
                    subscription_id=subscription_id,
                    due_date=datetime.strptime(due_date["due_date"], '%d-%m-%Y').date(),
                    amount=due_date.get("amount", 0),  # Amount from due dates
                    recurrence=due_date["recurrence"],  # Corrected to match model
                    duration_from=datetime.strptime(due_date["duration_from"], '%d-%m-%Y').date(),
                    duration_upto=datetime.strptime(due_date["duration_upto"], '%d-%m-%Y').date(),
                    mail_status="pending",  # Default mail status
                )
                session.add(subscription_due_date)
            
            session.commit()  # Commit after all due dates are added
            logger.info(f"Due dates saved to database for subscription: {subscription_id}")
        except Exception as e:
            logger.error(f"Error saving due dates to DB for subscription {subscription_id}: {e}")
            session.rollback()  # Rollback in case of error
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

    @staticmethod
    async def fetch_latest_invoice(subscription_id: str):
        """
        Fetch the latest invoice for a subscription from Razorpay.
        """
        try:
            logger.info(f"Initiating request to fetch invoices for subscription_id: {subscription_id}")
            async with httpx.AsyncClient(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET)) as client:
                response = await client.get(f"{BASE_URL}/invoices?subscription_id={subscription_id}")
                
                if response.status_code != 200:
                    logger.error(f"Error fetching invoices: {response.text}")
                    raise HTTPException(status_code=response.status_code, detail="Error fetching invoices")
                
                data = response.json()
                invoices = data.get("items", [])
                
                if not invoices:
                    logger.info("No invoices found for the subscription.")
                    return {"message": "Invoice not generated yet. Please contact customer care."}

                # Find the latest invoice based on 'date'
                latest_invoice = max(invoices, key=lambda x: x.get("date", 0))
                
                # Extract required details
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
        


class SubscriptionNotificationService:

    @staticmethod
    async def fetch_latest_invoice(subscription_id: str):
        try:
            logger.info(f"Initiating request to fetch invoices for subscription_id: {subscription_id}")
            
            # Step 1: Sending request to Razorpay's API
            async with httpx.AsyncClient(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET)) as client:
                response = await client.get(f"{BASE_URL}/invoices?subscription_id={subscription_id}")
                logger.info(f"Received response from Razorpay API for subscription_id: {subscription_id}, status code: {response.status_code}")

                # Step 2: Handle non-200 responses
                if response.status_code != 200:
                    logger.error(f"Error fetching invoices from Razorpay for subscription_id: {subscription_id}, Response: {response.text}")
                    raise HTTPException(status_code=response.status_code, detail="Error fetching invoices")

                # Step 3: Parsing Razorpay response
                data = response.json()
                invoices = data.get("items", [])
                logger.info(f"Number of invoices found: {len(invoices)} for subscription_id: {subscription_id}")

                # Step 4: Handle no invoices found
                if not invoices:
                    logger.warning(f"No invoices found for subscription_id: {subscription_id}")
                    return {"message": "Invoice not generated yet. Please contact customer care."}

                # Step 5: Find the latest invoice
                latest_invoice = max(invoices, key=lambda x: x.get("date", 0))
                logger.info(f"Latest invoice details identified for subscription_id: {subscription_id}: {latest_invoice}")

                # Step 6: Extract required details
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

                logger.info(f"Successfully extracted latest invoice details for subscription_id: {subscription_id}")
                return latest_invoice_details

        except Exception as e:
            logger.error(f"Error in fetch_latest_invoice for subscription_id: {subscription_id}, Error: {e}")
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    @staticmethod
    async def check_invoice_generated_or_not_for_today(session):
        """Check invoices for subscriptions with due date today or yesterday."""
        try:
            today = datetime.utcnow().date()
            yesterday = today - timedelta(days=1)
            logger.info(f"Target dates for invoice check: Today: {today}, Yesterday: {yesterday}")

            # Step 1: Query database for due subscriptions
            logger.info("Fetching subscriptions due today or yesterday from the database.")
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
            logger.info(f"Number of upcoming subscriptions found: {len(upcoming_subscriptions)}")

            if not upcoming_subscriptions:
                logger.info("No upcoming subscriptions found for the target dates.")
                return []

            reminder_list = []

            # Step 2: Iterate through subscriptions and check invoices
            for due_date, customer in upcoming_subscriptions:
                logger.info(f"Processing subscription_id: {due_date.subscription_id} for due date: {due_date.due_date}")

                # Fetch the latest invoice for the subscription
                try:
                    invoice_details = await SubscriptionNotificationService.fetch_latest_invoice(due_date.subscription_id)
                except Exception as e:
                    logger.error(f"Error fetching invoice for subscription_id: {due_date.subscription_id}, Error: {e}")
                    continue

                # Log due date and Razorpay response details
                logger.info(f"DB Due Date: {due_date.due_date}, Razorpay Invoice Date: {invoice_details.get('date', 'No invoice')}")

                # Step 3: Process invoice status
                if "message" in invoice_details:
                    logger.warning(f"No invoice found for subscription_id: {due_date.subscription_id}, marking as Payment Due.")
                    if due_date.due_date < today:
                        reminder_list.append({
                            "subscription_id": due_date.subscription_id,
                            "customer_name": customer.full_name,
                            "customer_email": customer.email,
                            "due_date": due_date.due_date,
                            "amount per reccurence": due_date.amount,
                            "duration_from": due_date.duration_from,
                            "duration_upto": due_date.duration_upto,
                            "status": "Due date passed, please pay",
                            "message": invoice_details["message"]
                        })
                    else:
                        reminder_list.append({
                            "subscription_id": due_date.subscription_id,
                            "customer_name": customer.full_name,
                            "customer_email": customer.email,
                            "due_date": due_date.due_date,
                            "amount per reccurence": due_date.amount,
                            "duration_from": due_date.duration_from,
                            "duration_upto": due_date.duration_upto,
                            "status": "Payment is due",
                            "message": invoice_details["message"]
                        })
                else:
                    logger.info(f"Invoice exists for subscription_id: {due_date.subscription_id}, marking as Paid.")
                    reminder_list.append({
                        "customer_name": customer.full_name,
                        "customer_email": customer.email,
                        "duration_from": due_date.duration_from,
                        "duration_upto": due_date.duration_upto,
                        "subscription_id": due_date.subscription_id,
                        "status": "Paid",
                        "invoice_details": invoice_details
                    })

            logger.info("Completed processing all subscriptions.")
            return reminder_list

        except Exception as e:
            logger.error(f"Error in check_invoice_generated_or_not_for_today: {e}")
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


    @staticmethod
    async def check_overdue_subscriptions(session):
        """Check subscriptions that are more than 7 days overdue and invoice is not generated or is older than 7 days."""
        try:
            today = datetime.utcnow().date()
            ten_days_ago = today - timedelta(days=10)
            seven_days_ago = today - timedelta(days=7)
            logger.info(f"Target dates for overdue subscription check: Ten days ago: {ten_days_ago}, Seven days ago: {seven_days_ago}, Today: {today}")

            # Step 1: Query the database for subscriptions with due date older than 7 days
            logger.info("Fetching subscriptions that are overdue by more than 7 days and have no invoice from the database.")
            overdue_subscriptions = (
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
                    cast(SubscriptionDueDate.due_date, Date) < seven_days_ago
                )
                .all()
            )
            logger.info(f"Number of overdue subscriptions found: {len(overdue_subscriptions)}")

            if not overdue_subscriptions:
                logger.info("No overdue subscriptions found that are more than 7 days old.")
                return []

            reminder_list = []

            # Step 2: Iterate through overdue subscriptions and check invoice status
            for due_date, customer in overdue_subscriptions:
                logger.info(f"Processing overdue subscription_id: {due_date.subscription_id} with due date: {due_date.due_date}")

                # Fetch the latest invoice for the subscription, only if it's within the last 10 days
                try:
                    invoice_details = await SubscriptionNotificationService.fetch_latest_invoice(due_date.subscription_id)
                except Exception as e:
                    logger.error(f"Error fetching invoice for subscription_id: {due_date.subscription_id}, Error: {e}")
                    continue

                # Log due date and Razorpay response details
                invoice_date = invoice_details.get("date")
                if invoice_date:
                    invoice_date = datetime.utcfromtimestamp(invoice_date).date()

                logger.info(f"DB Due Date: {due_date.due_date}, Razorpay Invoice Date: {invoice_date if invoice_date else 'No invoice'}")

                # Step 3: Check if invoice is within the last 10 days
                if invoice_date and invoice_date >= ten_days_ago:
                    # Invoice is within the last 10 days
                    # Check if invoice is within the 7-day range (near payment)
                    if invoice_date >= seven_days_ago:
                        # Invoice is within 7 days range, so assume user has paid
                        logger.info(f"Invoice generated within the last 7 days for subscription_id: {due_date.subscription_id}, user has paid.")
                        continue  # Skip this subscription, as it has been paid

                    # If the invoice is older than 7 days and the due date has passed 7 days
                    logger.warning(f"Invoice generated within the last 10 days but not within the 7-day range for subscription_id: {due_date.subscription_id}. Marking as Payment Due.")
                    reminder_list.append({
                        "subscription_id": due_date.subscription_id,
                        "due_date": due_date.due_date,
                        "amount_per_recurrence": due_date.amount,
                        "duration_from": due_date.duration_from,
                        "duration_upto": due_date.duration_upto,
                        "status": "Invoice generated but overdue, subscription will be canceled",
                        "message": "Your subscription is overdue by more than 7 days. To continue your services, please clear the dues."
                    })
                else:
                    # If no invoice or the invoice is older than 10 days
                    logger.warning(f"No invoice or invoice is older than 10 days for subscription_id: {due_date.subscription_id}, marking as Payment Due.")
                    reminder_list.append({
                        "subscription_id": due_date.subscription_id,
                        "due_date": due_date.due_date,
                        "amount_per_recurrence": due_date.amount,
                        "duration_from": due_date.duration_from,
                        "duration_upto": due_date.duration_upto,
                        "status": "Invoice not generated or outdated, subscription will be canceled",
                        "message": "Your subscription is overdue by more than 7 days. To continue your services, please clear the dues."
                    })

            logger.info("Completed processing all overdue subscriptions.")
            return reminder_list

        except Exception as e:
            logger.error(f"Error in check_overdue_subscriptions: {e}")
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
