import requests

def retrieve_plans(plans_list):
    # Your Paystack secret key
    secret_key = "YOUR_SECRET_KEY"

    # URL for retrieving a plan by its ID or code
    base_url = "https://api.paystack.co/plan/"

    # Headers for authorization
    headers = {
        "Authorization": f"Bearer {secret_key}"
    }

    # List to store retrieved plans
    retrieved_plans = []

    for plan_id_or_code in plans_list:
        # Construct URL for each plan
        url = base_url + str(plan_id_or_code)

        # Make a GET request to retrieve the plan details
        response = requests.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            # Extract plan details from the response
            plan_data = response.json().get("data")
            retrieved_plans.append(plan_data)
        else:
            print(f"Failed to retrieve plan with ID/Code: {plan_id_or_code}")

    return retrieved_plans

# Example list of plan IDs or codes
plans_to_retrieve = ["PLN_code1", "PLN_code2", "PLN_code3", "PLN_code4"]

# Retrieve plans
retrieved_plans = retrieve_plans(plans_to_retrieve)

# Process retrieved plans
for plan in retrieved_plans:
    print(plan)  # Process or use the retrieved plans as needed
