select * from customer
select * from Subscription



-- Create the Customer table
CREATE TABLE Customer (
    customer_id VARCHAR(255) NOT NULL PRIMARY KEY,
    subscription_id VARCHAR(255) NULL,
    plan_id VARCHAR(255) NULL,
    total_recurrence INT NULL,
    current_recurrence INT NULL,
    updated_on DATETIME NULL,
    amount_per_recurrence DECIMAL(18, 2) NULL,
    full_name VARCHAR(255) NULL,
    phone_number VARCHAR(15) NULL,
    email VARCHAR(255) NULL
);

-- Create the Invoice table
CREATE TABLE Invoice (
    invoice_id VARCHAR(255) NOT NULL PRIMARY KEY,
    customer_id VARCHAR(255) NULL,
    subscription_id VARCHAR(255) NULL,
    amount DECIMAL(18, 2) NULL,
    paid_on DATETIME NULL,
    status VARCHAR(50) NULL,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
    FOREIGN KEY (subscription_id) REFERENCES Subscription(subscription_id)
);

-- Create the Subscription table
CREATE TABLE Subscription (
    subscription_id VARCHAR(255) NOT NULL PRIMARY KEY,
    customer_id VARCHAR(255) NULL,
    plan_id VARCHAR(255) NULL,
    start_date DATE NULL,
    end_date DATE NULL,
    status VARCHAR(20) NULL,
    created_at DATETIME2 DEFAULT GETDATE(),
    last_updated DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
);