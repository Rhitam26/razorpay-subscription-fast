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


-- Create the Subscription DueDate table with automated due_id starting from 34321
CREATE TABLE Subscription_DueDate (
    due_id INT NOT NULL PRIMARY KEY IDENTITY(34321, 1), -- Start from 34321 and increment by 1 for each new entry
    subscription_id VARCHAR(255) NOT NULL,              -- Reference to the Subscription table
    due_date DATE NOT NULL,                              -- The date when the payment is due
    amount DECIMAL(18, 2) NOT NULL,                      -- Amount due on the due date
    recurrence INT NOT NULL,                             -- The recurrence cycle (e.g., 1, 2, 3,...)
    mail_status VARCHAR(50) NULL,                        -- Email status (e.g., "pending", "sent", "overdue")
    duration_from DATE NULL,                             -- Start date for the duration
    duration_upto DATE NULL,                             -- End date for the duration
    FOREIGN KEY (subscription_id) REFERENCES Subscription(subscription_id)  -- Link to the Subscription table
);
