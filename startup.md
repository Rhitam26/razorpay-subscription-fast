1. Create a virtual env `python -m venv myenv`
2. Activate virtual env `myenv\scripts\activate`
3. Install Dependencies `pip install -r requirements.txt`
4. Start server `uvicorn main:app --reload`



------------------------------------------------------------------------------
# RazorpayService Documentation

## Purpose  
Manages interaction with the Razorpay API, including creating customers, plans, and subscriptions.


## Static Methods

### 1. **`create_or_fetch_customer`**  
- Checks if a customer exists in the database.  
- Creates a new customer on Razorpay if not found.  
- Saves or updates the record in the database.

### 2. **`create_plan_on_razorpay`**  
- Creates a subscription plan on Razorpay using provided input data.

### 3. **`create_subscription_on_razorpay`**  
- Creates a subscription for a specific plan on Razorpay.

### 4. **`save_subscription_to_db`**  
- Saves a subscription record to the database for future reference.

---

## Code Structure

### **main.py**  

**Purpose:**  
Entry point for the FastAPI application.

#### Endpoints  

- **`/create-subscription/`**  
  - Accepts user input as a `PlanInput` model.  
  - Interacts with the `RazorpayService` methods to handle customer creation, plan creation, and subscription creation.  
  - Returns a `FinalResponse` containing subscription and customer details.

#### Key Operations  
- Uses dependency injection (`Depends`) to manage the database session.  
- Implements logging to track API calls and application behavior.  
- Handles exceptions gracefully with `HTTPException`.

---

### **razorpay_services.py**  

**Purpose:**  
Implements business logic for interacting with the Razorpay API and database.

#### Class: RazorpayService  
- All methods are `@staticmethod`, making the logic reusable without needing an instance of the class.  
- Handles Razorpay API authentication and error handling.  
- Modular design enables seamless integration with FastAPI or other frameworks.

---

### **models.py**  

**Purpose:**  
Defines the data models for database and request/response handling.

#### Key Models  

1. **`PlanInput`**  
   - Represents the incoming request payload for creating subscriptions.

2. **`Customer`**  
   - ORM model for storing customer data.

3. **`Subscription`**  
   - ORM model for storing subscription details.

4. **`FinalResponse`**  
   - Represents the API response containing subscription and customer information.
