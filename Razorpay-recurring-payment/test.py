# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from datetime import datetime, timedelta
# import logging
# from typing import List, Dict
# import httpx
# from models import SubscriptionDueDate, Customer, Subscription
# from email_service import EmailService  # Assuming you have an email service

# router = APIRouter()
# logger = logging.getLogger(__name__)

# class SubscriptionNotificationService:
#     def __init__(self, session: Session):
#         self.session = session
#         self.email_service = EmailService()  # Initialize your email service

#     async def process_due_date_notifications(self):
#         """Daily cron job to process due date notifications and invoices"""
#         try:
#             today = datetime.now().date()
#             two_days_from_now = today + timedelta(days=2)
            
#             # Fetch all relevant subscription due dates
#             due_dates = (
#                 self.session.query(SubscriptionDueDate)
#                 .join(Subscription, SubscriptionDueDate.subscription_id == Subscription.subscription_id)
#                 .join(Customer, Subscription.customer_id == Customer.customer_id)
#                 .filter(
#                     (SubscriptionDueDate.due_date == today) |  # Due today
#                     (SubscriptionDueDate.due_date == two_days_from_now),  # Due in 2 days
#                     SubscriptionDueDate.mail_status == 'pending'  # Only pending notifications
#                 )
#                 .all()
#             )

#             for due_date in due_dates:
#                 try:
#                     # Get customer details
#                     customer = (
#                         self.session.query(Customer)
#                         .join(Subscription, Customer.customer_id == Subscription.customer_id)
#                         .filter(Subscription.subscription_id == due_date.subscription_id)
#                         .first()
#                     )

#                     if not customer:
#                         logger.error(f"Customer not found for subscription {due_date.subscription_id}")
#                         continue

#                     # If due date is today, check invoice and send payment notification
#                     if due_date.due_date == today:
#                         await self._process_due_today(due_date, customer)
                    
#                     # If due date is in 2 days, send reminder
#                     elif due_date.due_date == two_days_from_now:
#                         await self._process_reminder(due_date, customer)

#                 except Exception as e:
#                     logger.error(f"Error processing due date {due_date.id}: {str(e)}")
#                     continue

#             return {"message": "Notification processing completed"}

#         except Exception as e:
#             logger.error(f"Error in process_due_date_notifications: {str(e)}")
#             raise HTTPException(status_code=500, detail=str(e))

#     async def _process_due_today(self, due_date: SubscriptionDueDate, customer: Customer):
#         """Process subscriptions due today"""
#         try:
#             # Fetch invoice from Razorpay
#             invoice_details = await RazorpayService.fetch_latest_invoice(due_date.subscription_id)
            
#             if not invoice_details:
#                 logger.error(f"No invoice found for subscription {due_date.subscription_id}")
#                 return

#             # Check if invoice is paid
#             is_paid = invoice_details.get('status') == 'paid'
#             payment_date = invoice_details.get('paid_at')
#             invoice_date = invoice_details.get('date')

#             if is_paid and payment_date and invoice_date:
#                 # Send payment confirmation
#                 await self._send_payment_confirmation(
#                     customer.email,
#                     invoice_details,
#                     due_date
#                 )
#             else:
#                 # Send payment due notification
#                 await self._send_payment_due_notification(
#                     customer.email,
#                     due_date,
#                     invoice_details
#                 )

#             # Update mail status
#             due_date.mail_status = 'sent'
#             self.session.commit()

#         except Exception as e:
#             logger.error(f"Error processing due today for {due_date.id}: {str(e)}")
#             raise

#     async def _process_reminder(self, due_date: SubscriptionDueDate, customer: Customer):
#         """Process reminders for subscriptions due in 2 days"""
#         try:
#             # Send reminder email
#             await self._send_reminder_notification(
#                 customer.email,
#                 due_date,
#                 customer
#             )

#             # Update mail status
#             due_date.mail_status = 'reminder_sent'
#             self.session.commit()

#         except Exception as e:
#             logger.error(f"Error processing reminder for {due_date.id}: {str(e)}")
#             raise

#     async def _send_payment_confirmation(self, email: str, invoice_details: Dict, due_date: SubscriptionDueDate):
#         """Send payment confirmation email"""
#         subject = "Payment Confirmation"
#         content = {
#             "invoice_number": invoice_details.get("invoice_number"),
#             "amount_paid": invoice_details.get("amount_paid"),
#             "payment_date": datetime.fromtimestamp(invoice_details.get("paid_at")).strftime("%Y-%m-%d"),
#             "subscription_id": due_date.subscription_id,
#             "duration": f"{due_date.duration_from} to {due_date.duration_upto}"
#         }
#         await self.email_service.send_email(email, subject, "payment_confirmation", content)

#     async def _send_payment_due_notification(self, email: str, due_date: SubscriptionDueDate, invoice_details: Dict):
#         """Send payment due notification"""
#         subject = "Payment Due Today"
#         content = {
#             "amount_due": invoice_details.get("amount_due"),
#             "due_date": due_date.due_date.strftime("%Y-%m-%d"),
#             "subscription_id": due_date.subscription_id,
#             "duration": f"{due_date.duration_from} to {due_date.duration_upto}",
#             "payment_link": invoice_details.get("short_url")
#         }
#         await self.email_service.send_email(email, subject, "payment_due", content)

#     async def _send_reminder_notification(self, email: str, due_date: SubscriptionDueDate, customer: Customer):
#         """Send payment reminder notification"""
#         subject = "Payment Due Reminder"
#         content = {
#             "customer_name": customer.full_name,
#             "amount_due": due_date.amount,
#             "due_date": due_date.due_date.strftime("%Y-%m-%d"),
#             "subscription_id": due_date.subscription_id,
#             "duration": f"{due_date.duration_from} to {due_date.duration_upto}"
#         }
#         await self.email_service.send_email(email, subject, "payment_reminder", content)

# # FastAPI endpoint for the cron job
# @router.post("/process-notifications")
# async def process_notifications(session: Session = Depends(get_db)):
#     service = SubscriptionNotificationService(session)
#     return await service.process_due_date_notifications()




# #----------------------------
# Subscription Notification
# -----------------------------
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from datetime import datetime, timedelta
# import logging
# from typing import List, Dict
# import httpx
# from models import SubscriptionDueDate, Customer, Subscription
# from email_service import EmailService  # Assuming you have an email service

# router = APIRouter()
# logger = logging.getLogger(__name__)

# class SubscriptionNotificationService:
#     def __init__(self, session: Session):
#         self.session = session
#         self.email_service = EmailService()  # Initialize your email service

#     async def process_due_date_notifications(self):
#         """Daily cron job to process due date notifications and invoices"""
#         try:
#             today = datetime.now().date()
#             two_days_from_now = today + timedelta(days=2)
            
#             # Fetch all relevant subscription due dates
#             due_dates = (
#                 self.session.query(SubscriptionDueDate)
#                 .join(Subscription, SubscriptionDueDate.subscription_id == Subscription.subscription_id)
#                 .join(Customer, Subscription.customer_id == Customer.customer_id)
#                 .filter(
#                     (SubscriptionDueDate.due_date == today) |  # Due today
#                     (SubscriptionDueDate.due_date == two_days_from_now),  # Due in 2 days
#                     SubscriptionDueDate.mail_status == 'pending'  # Only pending notifications
#                 )
#                 .all()
#             )

#             for due_date in due_dates:
#                 try:
#                     # Get customer details
#                     customer = (
#                         self.session.query(Customer)
#                         .join(Subscription, Customer.customer_id == Subscription.customer_id)
#                         .filter(Subscription.subscription_id == due_date.subscription_id)
#                         .first()
#                     )

#                     if not customer:
#                         logger.error(f"Customer not found for subscription {due_date.subscription_id}")
#                         continue

#                     # If due date is today, check invoice and send payment notification
#                     if due_date.due_date == today:
#                         await self._process_due_today(due_date, customer)
                    
#                     # If due date is in 2 days, send reminder
#                     elif due_date.due_date == two_days_from_now:
#                         await self._process_reminder(due_date, customer)

#                 except Exception as e:
#                     logger.error(f"Error processing due date {due_date.id}: {str(e)}")
#                     continue

#             return {"message": "Notification processing completed"}

#         except Exception as e:
#             logger.error(f"Error in process_due_date_notifications: {str(e)}")
#             raise HTTPException(status_code=500, detail=str(e))

#     async def _process_due_today(self, due_date: SubscriptionDueDate, customer: Customer):
#         """Process subscriptions due today"""
#         try:
#             # Fetch invoice from Razorpay
#             invoice_details = await RazorpayService.fetch_latest_invoice(due_date.subscription_id)
            
#             if not invoice_details:
#                 logger.error(f"No invoice found for subscription {due_date.subscription_id}")
#                 return

#             # Check if invoice is paid
#             is_paid = invoice_details.get('status') == 'paid'
#             payment_date = invoice_details.get('paid_at')
#             invoice_date = invoice_details.get('date')

#             if is_paid and payment_date and invoice_date:
#                 # Send payment confirmation
#                 await self._send_payment_confirmation(
#                     customer.email,
#                     invoice_details,
#                     due_date
#                 )
#             else:
#                 # Send payment due notification
#                 await self._send_payment_due_notification(
#                     customer.email,
#                     due_date,
#                     invoice_details
#                 )

#             # Update mail status
#             due_date.mail_status = 'sent'
#             self.session.commit()

#         except Exception as e:
#             logger.error(f"Error processing due today for {due_date.id}: {str(e)}")
#             raise

#     async def _process_reminder(self, due_date: SubscriptionDueDate, customer: Customer):
#         """Process reminders for subscriptions due in 2 days"""
#         try:
#             # Send reminder email
#             await self._send_reminder_notification(
#                 customer.email,
#                 due_date,
#                 customer
#             )

#             # Update mail status
#             due_date.mail_status = 'reminder_sent'
#             self.session.commit()

#         except Exception as e:
#             logger.error(f"Error processing reminder for {due_date.id}: {str(e)}")
#             raise

#     async def _send_payment_confirmation(self, email: str, invoice_details: Dict, due_date: SubscriptionDueDate):
#         """Send payment confirmation email"""
#         subject = "Payment Confirmation"
#         content = {
#             "invoice_number": invoice_details.get("invoice_number"),
#             "amount_paid": invoice_details.get("amount_paid"),
#             "payment_date": datetime.fromtimestamp(invoice_details.get("paid_at")).strftime("%Y-%m-%d"),
#             "subscription_id": due_date.subscription_id,
#             "duration": f"{due_date.duration_from} to {due_date.duration_upto}"
#         }
#         await self.email_service.send_email(email, subject, "payment_confirmation", content)

#     async def _send_payment_due_notification(self, email: str, due_date: SubscriptionDueDate, invoice_details: Dict):
#         """Send payment due notification"""
#         subject = "Payment Due Today"
#         content = {
#             "amount_due": invoice_details.get("amount_due"),
#             "due_date": due_date.due_date.strftime("%Y-%m-%d"),
#             "subscription_id": due_date.subscription_id,
#             "duration": f"{due_date.duration_from} to {due_date.duration_upto}",
#             "payment_link": invoice_details.get("short_url")
#         }
#         await self.email_service.send_email(email, subject, "payment_due", content)

#     async def _send_reminder_notification(self, email: str, due_date: SubscriptionDueDate, customer: Customer):
#         """Send payment reminder notification"""
#         subject = "Payment Due Reminder"
#         content = {
#             "customer_name": customer.full_name,
#             "amount_due": due_date.amount,
#             "due_date": due_date.due_date.strftime("%Y-%m-%d"),
#             "subscription_id": due_date.subscription_id,
#             "duration": f"{due_date.duration_from} to {due_date.duration_upto}"
#         }
#         await self.email_service.send_email(email, subject, "payment_reminder", content)

# # FastAPI endpoint for the cron job
# @router.post("/process-notifications")
# async def process_notifications(session: Session = Depends(get_db)):
#     service = SubscriptionNotificationService(session)
#     return await service.process_due_date_notifications()






# -------------------------

# API for 2-Day Prior Due Date Reminders:
# --------------------------------
# @staticmethod
# async def get_upcoming_due_date_subscriptions(session):
#     """Get all subscriptions with due dates in 2 days"""
#     try:
#         # Calculate the target date (2 days from now)
#         target_date = datetime.now().date() + timedelta(days=2)
        
#         # Query to get subscriptions and customer details
#         upcoming_subscriptions = (
#             session.query(
#                 SubscriptionDueDate,
#                 Customer
#             )
#             .join(
#                 Subscription, 
#                 SubscriptionDueDate.subscription_id == Subscription.subscription_id
#             )
#             .join(
#                 Customer,
#                 Subscription.customer_id == Customer.customer_id
#             )
#             .filter(
#                 SubscriptionDueDate.due_date == target_date,
#                 SubscriptionDueDate.mail_status == 'pending'
#             )
#             .all()
#         )
        
#         # Format the response data
#         reminder_list = [{
#             "customer_email": customer.email,
#             "customer_name": customer.full_name,
#             "subscription_id": due_date.subscription_id,
#             "amount_due": due_date.amount,
#             "due_date": due_date.due_date,
#             "duration_from": due_date.duration_from,
#             "duration_upto": due_date.duration_upto,
#         } for due_date, customer in upcoming_subscriptions]
        
#         return reminder_list
# ---------------------------------------
# API for Due Date Invoice Check:
# ----------------------------------------
# @staticmethod
# async def check_due_date_invoices(session):
#     """Check invoices for subscriptions due today"""
#     try:
#         # Get today's subscriptions
#         today = datetime.now().date()
        
#         # Query subscriptions due today
#         due_subscriptions = (
#             session.query(
#                 SubscriptionDueDate,
#                 Customer
#             )
#             .join(
#                 Subscription,
#                 SubscriptionDueDate.subscription_id == Subscription.subscription_id
#             )
#             .join(
#                 Customer,
#                 Subscription.customer_id == Customer.customer_id
#             )
#             .filter(
#                 SubscriptionDueDate.due_date == today,
#                 SubscriptionDueDate.mail_status != 'invoice_generated'
#             )
#             .all()
#         )

#         reminder_list = []
        
#         # Check each subscription's invoice status
#         for due_date, customer in due_subscriptions:
#             # Fetch latest invoice from Razorpay
#             invoice_details = await RazorpayService.fetch_latest_invoice(due_date.subscription_id)
            
#             # If no invoice generated or not paid
#             if (not invoice_details or 
#                 invoice_details.get('message') == "Invoice not generated yet. Please contact customer care."):
#                 reminder_list.append({
#                     "customer_email": customer.email,
#                     "customer_name": customer.full_name,
#                     "subscription_id": due_date.subscription_id,
#                     "amount_due": due_date.amount,
#                     "due_date": due_date.due_date,
#                     "status": "invoice_pending"
#                 })
        
#         return reminder_list
# ---------------------------------------
# API for Payment Pending Reminders:
# -------------------------------------------
# @staticmethod
# async def check_payment_pending_invoices(session):
#     """Check for pending payments on generated invoices"""
#     try:
#         # Get today's subscriptions
#         today = datetime.now().date()
        
#         # Query subscriptions due today
#         due_subscriptions = (
#             session.query(
#                 SubscriptionDueDate,
#                 Customer
#             )
#             .join(
#                 Subscription,
#                 SubscriptionDueDate.subscription_id == Subscription.subscription_id
#             )
#             .join(
#                 Customer,
#                 Subscription.customer_id == Customer.customer_id
#             )
#             .filter(
#                 SubscriptionDueDate.due_date == today,
#                 SubscriptionDueDate.mail_status == 'invoice_generated'
#             )
#             .all()
#         )

#         payment_pending_list = []
        
#         for due_date, customer in due_subscriptions:
#             # Fetch latest invoice
#             invoice_details = await RazorpayService.fetch_latest_invoice(due_date.subscription_id)
            
#             # Check if invoice exists and payment is pending
#             if (invoice_details and 
#                 isinstance(invoice_details, dict) and
#                 invoice_details.get('status') != 'paid'):
                
#                 payment_pending_list.append({
#                     "customer_email": customer.email,
#                     "customer_name": customer.full_name,
#                     "subscription_id": due_date.subscription_id,
#                     "invoice_id": invoice_details.get('id'),
#                     "amount_due": invoice_details.get('amount_due'),
#                     "invoice_url": invoice_details.get('short_url'),
#                     "status": "payment_pending"
#                 })
        
#         return payment_pending_list
from datetime import datetime, timedelta
import logging
from sqlalchemy import create_engine, cast, Date
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from models import SubscriptionDueDate, Subscription, Customer

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

def get_upcoming_2DAYS_due_date_subscriptions(session: Session):
    try:
        target_date = datetime.utcnow().date() + timedelta(days=2)
        logger.info(f"Target date for query: {target_date}")

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
                cast(SubscriptionDueDate.due_date, Date) == target_date,
                SubscriptionDueDate.mail_status == 'pending'
            )
            .all()
        )

        if not upcoming_subscriptions:
            logger.info("No upcoming subscriptions found for the target date.")
            return []

        reminder_list = [{
            "customer_email": customer.email,
            "customer_name": customer.full_name,
            "subscription_id": due_date.subscription_id,
            "amount_due": due_date.amount,
            "due_date": due_date.due_date.strftime('%Y-%m-%d'),
            "duration_from": due_date.duration_from.strftime('%Y-%m-%d'),
            "duration_upto": due_date.duration_upto.strftime('%Y-%m-%d'),
        } for due_date, customer in upcoming_subscriptions]

        return reminder_list
    except Exception as e:
        logger.error(f"Error fetching upcoming subscriptions: {str(e)}")
        raise


# def check_invoice_genrated_or_not_for_today(session: Session):
#     try:
#         target_date = datetime.utcnow().date() 
#         logger.info(f"Target date for query: {target_date}")

#         upcoming_subscriptions = (
#             session.query(
#                 SubscriptionDueDate,
#                 Customer
#             )
#             .join(
#                 Subscription,
#                 SubscriptionDueDate.subscription_id == Subscription.subscription_id
#             )
#             .join(
#                 Customer,
#                 Subscription.customer_id == Customer.customer_id
#             )
#             .filter(
#                 cast(SubscriptionDueDate.due_date, Date) == target_date
#             )
#             .all()
#         )

#         if not upcoming_subscriptions:
#             logger.info("No upcoming subscriptions found for the target date.")
#             return []

#         reminder_list = [{
#             "customer_email": customer.email,
#             "customer_name": customer.full_name,
#             "subscription_id": due_date.subscription_id,
#             "amount_due": due_date.amount,
#             "due_date": due_date.due_date.strftime('%Y-%m-%d'),
#             "duration_from": due_date.duration_from.strftime('%Y-%m-%d'),
#             "duration_upto": due_date.duration_upto.strftime('%Y-%m-%d'),
#         } for due_date, customer in upcoming_subscriptions]

#         return reminder_list
#     except Exception as e:
#         logger.error(f"Error fetching upcoming subscriptions: {str(e)}")
#         raise


def main():
    session = SessionLocal()
    try:
        reminders =  check_invoice_genrated_or_not_for_today(session)
        if reminders:
            for reminder in reminders:
                print(f"Customer: {reminder['customer_name']} ({reminder['customer_email']})")
                print(f"  Subscription ID: {reminder['subscription_id']}")
                print(f"  Amount Due: {reminder['amount_due']}")
                print(f"  Due Date: {reminder['due_date']}")
                print(f"  Duration: {reminder['duration_from']} to {reminder['duration_upto']}")
                print()
        else:
            print("No upcoming due date subscriptions found.")
    except Exception as e:
        logger.error(f"Error occurred: {e}")
    finally:
        session.close()
        logger.info("Database session closed.")

if __name__ == "__main__":
    main()
