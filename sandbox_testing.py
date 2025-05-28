import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_access_token():
    """Get LWA access token using refresh token"""
    token_url = "https://api.amazon.com/auth/o2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": os.getenv('SANDBOX_REFRESH_TOKEN'),
        "client_id": os.getenv('SANDBOX_CLIENT_ID'),
        "client_secret": os.getenv('SANDBOX_CLIENT_SECRET')
    }
    response = requests.post(token_url, data=data)
    response.raise_for_status()  # Raise errors for bad status codes
    return response.json()['access_token']

def load_products(file_path='products.json'):
    """Load products from JSON file and adapt for sandbox"""
    with open(file_path) as f:
        products = json.load(f)
    
    # Sandbox-specific modifications
    for product in products:
        product['product_data']['requirements'] = 'LISTING'
        product['product_data']['attributes']['brand'] = 'SANDBOX_BRAND'
        product['product_data']['attributes']['manufacturer'] = 'SANDBOX_MFG'

        # Ensure minimum_price < standard_price
        std_price = product['product_data']['attributes']['standard_price']['value']
        min_price = product['product_data']['attributes']['minimum_price']['value']
        if min_price >= std_price:
            product['product_data']['attributes']['minimum_price']['value'] = std_price * 0.8

        product['product_data']['attributes']['main_image'] = {
            "link": "https://www.junglemug.com/cdn/shop/collections/Group_39892_5c108ecf-6033-4f13-934a-e6635d670c72.png?v=1737468874",  # Fake but sandbox-friendly URL
            "height": 500,
            "width": 500
            }
        
        # Ensure required fields for sandbox
        if product['product_data']['productType'] == 'SHOES':
            product['product_data']['attributes'].setdefault('size', '10')
        elif product['product_data']['productType'] == 'LUGGAGE':
            product['product_data']['attributes'].setdefault('size', 'Medium')
            
    return products

def create_sandbox_listings():
    """Create listings for all products in JSON file"""
    access_token = get_access_token()
    products = load_products()
    results = []
    
    for product in products:
        url = f"https://sandbox.sellingpartnerapi-eu.amazon.com/listings/2021-08-01/items/A1F83G8C2ARO7P/{product['sku']}"
        
        params = {
            "marketplaceIds": "A1F83G8C2ARO7P",
            "includedData": "issues"
        }
        
        headers = {
            "x-amz-access-token": access_token,
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        
        try:
            response = requests.put(url, params=params, json=product['product_data'], headers=headers)
            response_data = response.json()
            
            # Sandbox often returns generic SKU
            if response_data.get('sku') != product['sku']:
                response_data['original_sku'] = product['sku']
                
            results.append({
                'sku': product['sku'],
                'status': 'SUCCESS',
                'response': response_data
            })
        except Exception as e:
            results.append({
                'sku': product['sku'],
                'status': 'FAILED',
                'error': str(e)
            })
    
    return results

def get_listing(sku):
    """Get listing details for a specific SKU"""
    access_token = get_access_token()
    
    url = f"https://sandbox.sellingpartnerapi-eu.amazon.com/listings/2021-08-01/items/A1F83G8C2ARO7P/{sku}"
    params = {
        "marketplaceIds": "A1F83G8C2ARO7P",
        "includedData": "summaries"
    }
    
    headers = {
        "x-amz-access-token": access_token,
        "accept": "application/json"
    }
    
    response = requests.get(url, params=params, headers=headers)
    return response.json()

if __name__ == '__main__':
    # Create listings from JSON file
    creation_results = create_sandbox_listings()
    print("Creation Results:")
    for result in creation_results:
        print(f"SKU: {result['sku']} - {result['status']}")
        if 'response' in result:
            print(json.dumps(result['response'], indent=2))
        elif 'error' in result:
            print(f"Error: {result['error']}")
    
    # Check one listing as example
    print("\nListing Details for TEST_SKU_1:")
    print(json.dumps(get_listing("TEST_SKU_1"), indent=2))