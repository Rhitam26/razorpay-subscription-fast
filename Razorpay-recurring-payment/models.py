from pydantic import BaseModel, validator
from sqlalchemy import Column, String, Integer, Date, ForeignKey, DateTime, Float, Numeric
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime  # Import datetime module
from typing import List, Dict
Base = declarative_base()


#Database Models
class Customer(Base):
    __tablename__ = "Customer"
    customer_id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, unique=True, nullable=True)
    full_name = Column(String, nullable=False)
    subscription_id = Column(String)
    plan_id = Column(String)
    total_recurrence = Column(Integer)
    current_recurrence = Column(Integer)
    updated_on = Column(Date)
    amount_per_recurrence = Column(Integer)

    subscriptions = relationship("Subscription", back_populates="customer")


class Subscription(Base):
    __tablename__ = "Subscription"
    subscription_id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("Customer.customer_id"))
    plan_id = Column(String)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated=Column(DateTime)
    customer = relationship("Customer", back_populates="subscriptions")
    due_dates = relationship("SubscriptionDueDate", back_populates="subscription")  # Add this line

# class SubscriptionDueDate(Base):
#     __tablename__ = 'Subscription_DueDate'

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     subscription_id = Column(String, ForeignKey('Subscription.subscription_id'), nullable=False)  # Corrected to String
#     due_date = Column(DateTime, nullable=False)
#     amount = Column(Float, nullable=False)
#     recurrence_number = Column(Integer, nullable=False)
#     email_status = Column(String, default="Pending")
#     duration_from = Column(DateTime, nullable=False)
#     duration_upto = Column(DateTime, nullable=False)

#     # Relationship to Subscription
#     subscription = relationship("Subscription", back_populates="due_dates")

class SubscriptionDueDate(Base):
    __tablename__ = 'Subscription_DueDate'

    due_id = Column(Integer, primary_key=True, autoincrement=True)  # Matches SQL definition
    subscription_id = Column(String, ForeignKey('Subscription.subscription_id'), nullable=False)  # Correct
    due_date = Column(Date, nullable=False)  # Matches SQL definition
    amount = Column(Numeric(18, 2), nullable=False)  # Matches SQL definition
    recurrence = Column(Integer, nullable=False)  # Matches SQL definition
    mail_status = Column(String(50), nullable=True)  # Matches SQL definition
    duration_from = Column(Date, nullable=True)  # Matches SQL definition
    duration_upto = Column(Date, nullable=True)  # Matches SQL definition

    # Relationship to Subscription
    subscription = relationship("Subscription", back_populates="due_dates")


# Models for request/response

class PlanInput(BaseModel):
    full_name: str
    email: str
    phone_number: str
    period: str
    amount: int
    currency: str
    description: str
    start_at: str
    expire_by: str
    notes: dict = {}
    total_count: int  # Add the total_count field
    interval: int  # Interval for plan, e.g., 1 for every month, 3 for quarterly, etc.

    @validator('period')
    def validate_period(cls, v):
        allowed_periods = ["daily", "weekly", "monthly", "quarterly", "yearly"]
        if v not in allowed_periods:
            raise ValueError(f"Invalid period. Allowed values are: {', '.join(allowed_periods)}")
        return v


class FinalResponse(BaseModel):
    subscription_id: str
    customer_id: str
    message: str
    due_dates: List[Dict]

