import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

access_token = os.getenv('SANDBOX_ACCESS_TOKEN')

# 2. Make the listing request
def create_sandbox_listing():
    
    # Sandbox endpoint (note 'sandbox.' prefix)
    url = "https://sandbox.sellingpartnerapi-eu.amazon.com/listings/2021-08-01/items/ATVPDKIKX0DER/TEST_SKU_1"
    
    # Sandbox parameters
    params = {
        "marketplaceIds": "A1F83G8C2ARO7P",  # UK marketplace
        "includedData": "issues"
    }
    
    # Sandbox-specific payload (must use exact values)
    payload = {
        "productType": "SHOES",  # Must be a valid sandbox product type
        "requirements": "LISTING",  # Required for sandbox
        "attributes": {
            "item_name": "Test Shoes Sandbox",
            "brand": "SANDBOX_BRAND",  # Must use sandbox brand
            "manufacturer": "SANDBOX_MFG",
            "standard_price": {
                "value": 19.99,
                "currency": "GBP"
            }
        }
    }
    
    headers = {
        "x-amz-access-token": access_token,
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    
    response = requests.put(url, params=params, json=payload, headers=headers)
    return response.json()

# Run the request
result = create_sandbox_listing()
print(result)

def get_listing():
    
    url = "https://sandbox.sellingpartnerapi-eu.amazon.com/listings/2021-08-01/items/ATVPDKIKX0DER/GM-ZDPI-9B4E"
    params = {
        "marketplaceIds": "A1F83G8C2ARO7P",
        "includedData": "summaries"  # Request listing details
    }
    
    headers = {
        "x-amz-access-token": access_token,
        "accept": "application/json"
    }
    
    response = requests.get(url, params=params, headers=headers)
    return response.json()

print(get_listing())