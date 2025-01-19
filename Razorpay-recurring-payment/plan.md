Daily :
{
  "full_name": "Shuja851",
  "email": "shujatest851@yopmail.com",
  "phone_number": "7091264491",
  "period": "daily",
  "amount": 100,
  "currency": "INR",
  "description": "string",
  "start_at": "25-11-2025",
  "expire_by": "14-02-2027",
  "notes": {},
  "total_count": 1,
  "interval": 7
}

Weekly :

{
  "full_name": "Shuja851",
  "email": "shujatest851@yopmail.com",
  "phone_number": "709264491",
  "period": "weekly",
  "amount": 100,
  "currency": "INR",
  "description": "string",
  "start_at": "25-11-2025",
  "expire_by": "14-02-2027",
  "notes": {},
  "total_count": 1,
  "interval": 7
}

Period : daily, weekly, monthly, quarterly, yearly

Interval : This, combined with period, defines the frequency of the plan. If the billing cycle is 2 months, the value should be 2. For daily plans, the minimum value should be 7

total_count : The number of billing cycles for which the customer should be charged. For example, if a customer is buying a 1-year subscription billed on a bi-monthly basis, this value should be 6.

Response  : Paid_cout :This indicates the number of billing cycles for which the customer has already been charged. For example, 2.