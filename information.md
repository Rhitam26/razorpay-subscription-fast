# main.py---------------------------

## Overview
This document provides an overview of the APIs available in the project, including their endpoints, purposes, and usage.

## Endpoints

### 1. Create Subscription
**Endpoint:** `/create-subscription/`  
**Method:** `POST`  
**Description:** Creates a new subscription for a customer.  
**Request Model:** `PlanInput`  
**Response Model:** `FinalResponse`  
**Usage:**
- Accepts user input as a `PlanInput` model.
- Interacts with the `RazorpayService` methods to handle customer creation, plan creation, and subscription creation.
- Returns a `FinalResponse` containing subscription and customer details.

### 2. Fetch Customer Last Updated
**Endpoint:** `/customer-last-updated/`  
**Method:** `GET`  
**Description:** Fetches the last updated timestamp for a customer based on their email.  
**Query Parameter:** `email` (string)  
**Response:** JSON object containing the last updated timestamp and a message.  
**Usage:**
- Fetches the last updated timestamp for a customer using their email.
- Returns the timestamp and a success message.

### 3. Update Customer Data
**Endpoint:** `/update-customer-data/`  
**Method:** `GET`  
**Description:** Updates customer data based on their subscription ID.  
**Query Parameter:** `subscription_id` (string)  
**Response:** JSON object containing the updated data and a message.  
**Usage:**
- Fetches and updates customer data using the subscription ID.
- Returns the updated data and a success message.

### 4. Fetch Latest Invoice
**Endpoint:** `/latest-invoice/`  
**Method:** `GET`  
**Description:** Fetches the latest invoice for a given subscription ID.  
**Query Parameter:** `subscription_id` (string)  
**Response:** JSON object containing the latest invoice details and a message.  
**Usage:**
- Fetches the latest invoice for the given subscription ID.
- Returns the invoice details and a success message.

### 5. Check Subscription Invoice Status
**Endpoint:** `/subscription-invoice-status/`  
**Method:** `GET`  
**Description:** Checks if an invoice has been generated for the given subscription.  
**Response:** JSON object containing the invoice status and a message.  
**Usage:**
- Uses `SubscriptionNotificationService` to fetch the latest invoice.
- Returns the invoice status and a success message.

### 6. Check Overdue Subscriptions Status
**Endpoint:** `/overdue-subscriptions-status-7Days/`  
**Method:** `GET`  
**Description:** Checks overdue subscriptions where the due date is more than 7 days ago and no invoice has been generated.  
**Response:** JSON object containing the overdue subscription details and a message.  
**Usage:**
- Uses `SubscriptionNotificationService` to check overdue subscriptions.
- Returns the overdue subscription details and a success message.

## Models

### PlanInput
Represents the incoming request payload for creating subscriptions.
- `full_name` (str)
- `email` (str)
- `phone_number` (str)
- `period` (str)
- `amount` (int)
- `currency` (str)
- `description` (str)
- `start_at` (str)
- `expire_by` (str)
- `notes` (dict)
- `total_count` (int)
- `interval` (int)

### FinalResponse
Represents the API response containing subscription and customer information.
- `subscription_id` (str)
- `customer_id` (str)
- `message` (str)

## Services

### RazorpayService
Handles interaction with the Razorpay API and database operations.
- `create_or_fetch_customer`
- `create_plan_on_razorpay`
- `create_subscription_on_razorpay`
- `save_subscription_to_db`
- `generate_due_dates`
- `save_due_dates_to_db`
- `fetch_customer_last_updated_by_email`
- `update_customer_data_based_on_subscription`
- `fetch_latest_invoice`

### SubscriptionNotificationService
Handles notification services related to subscriptions.
- `fetch_latest_invoice`
- `check_invoice_generated_or_not_for_today`
- `check_overdue_subscriptions`

## Usage
To use these APIs, make HTTP requests to the specified endpoints with the required parameters and request bodies. The responses will contain the relevant data and messages as described above.

# Razorpay Services Documentation-----------------------------

## Overview
This document provides an overview of the services and methods available in the `razorpay_services.py` file, including their purposes and usage.

## Services

### RazorpayService
Handles interaction with the Razorpay API and database operations.

#### Methods

1. **create_or_fetch_customer**
   - **Description:** Creates a new customer on Razorpay or fetches an existing customer from the database.
   - **Parameters:** `customer_data` (dict)
   - **Returns:** Customer details (dict)

2. **create_plan_on_razorpay**
   - **Description:** Creates a new plan on Razorpay.
   - **Parameters:** `plan_data` (dict)
   - **Returns:** Plan details (dict)

3. **create_subscription_on_razorpay**
   - **Description:** Creates a new subscription on Razorpay.
   - **Parameters:** `subscription_data` (dict)
   - **Returns:** Subscription details (dict)

4. **save_subscription_to_db**
   - **Description:** Saves subscription details to the database.
   - **Parameters:** `subscription_data` (dict)
   - **Returns:** None

5. **generate_due_dates**
   - **Description:** Generates due dates for the subscription.
   - **Parameters:** `subscription_id` (str), `start_date` (datetime), `interval` (int), `total_count` (int)
   - **Returns:** List of due dates (list)

6. **save_due_dates_to_db**
   - **Description:** Saves due dates to the database.
   - **Parameters:** `due_dates` (list)
   - **Returns:** None

7. **fetch_customer_last_updated_by_email**
   - **Description:** Fetches the last updated timestamp for a customer based on their email.
   - **Parameters:** `email` (str)
   - **Returns:** Last updated timestamp (datetime)

8. **update_customer_data_based_on_subscription**
   - **Description:** Updates customer data based on their subscription ID.
   - **Parameters:** `subscription_id` (str)
   - **Returns:** Updated customer data (dict)

9. **fetch_latest_invoice**
   - **Description:** Fetches the latest invoice for a given subscription ID.
   - **Parameters:** `subscription_id` (str)
   - **Returns:** Invoice details (dict)

10. **check_invoice_generated_or_not_for_today**
    - **Description:** Checks if an invoice has been generated for the given subscription today.
    - **Parameters:** `subscription_id` (str)
    - **Returns:** Invoice status (bool)

11. **check_overdue_subscriptions**
    - **Description:** Checks overdue subscriptions where the due date is more than 7 days ago and no invoice has been generated.
    - **Parameters:** `db` (db_dependency)
    - **Returns:** List of overdue subscription details (list)
    - **Usage:**
      - Fetches overdue subscriptions from the database.
      - Iterates through overdue subscriptions and checks invoice status.
      - Logs due date and Razorpay response details.

## Usage
To use these services, instantiate the `RazorpayService` class and call the desired methods with the required parameters. The methods will interact with the Razorpay API and the database to perform the necessary operations.