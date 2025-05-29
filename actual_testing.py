import requests
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SPAPIListingManager:
    def __init__(self):
        self.rate_limit_remaining = 10.0  # Use float initially
        self.rate_limit_reset = 1.0
        self.base_url = "https://sellingpartnerapi-eu.amazon.com"  # Change region as needed
        self.marketplace_id = "A1F83G8C2ARO7P"  # UK marketplace, change as needed

    def get_access_token(self):
        """Get LWA access token using refresh token"""
        token_url = "https://api.amazon.com/auth/o2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": os.getenv('SP_API_REFRESH_TOKEN'),
            "client_id": os.getenv('SP_API_CLIENT_ID'),
            "client_secret": os.getenv('SP_API_CLIENT_SECRET')
        }
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        return response.json()['access_token']

    def check_rate_limit(self):
        """Check if we need to wait due to rate limits"""
        if self.rate_limit_remaining <= 1:
            print(f"Rate limit reached. Waiting {self.rate_limit_reset} seconds")
            time.sleep(self.rate_limit_reset)
            self.rate_limit_remaining = 10  # Reset after waiting

    def load_products(self, file_path='products.json'):
        """Load products from JSON file with production validation"""
        with open(file_path) as f:
            products = json.load(f)
        
        # Production-specific modifications
        for product in products:
            # Ensure all required fields are present
            if not all(k in product['product_data']['attributes'] for k in ['brand', 'manufacturer', 'item_name']):
                raise ValueError(f"Product {product['sku']} missing required attributes")
            
            # Validate prices
            std_price = product['product_data']['attributes']['standard_price']['value']
            min_price = product['product_data']['attributes']['minimum_price']['value']
            if min_price >= std_price:
                raise ValueError(f"Product {product['sku']} has minimum_price >= standard_price")
            
            # Validate image URL
            image_url = product['product_data']['attributes']['main_image']['link']
            if not image_url.startswith('https://'):
                raise ValueError(f"Product {product['sku']} has invalid image URL")
                
        return products

    def create_listing(self, product_data, sku, mode='VALIDATION_PREVIEW'):
        """Create or update a listing in production"""
        self.check_rate_limit()
        
        access_token = self.get_access_token()
        seller_id = os.getenv('UK_SELLER_ID')  # Add this to your .env
        
        url = f"{self.base_url}/listings/2021-08-01/items/{seller_id}/{sku}"
        
        params = {
            "marketplaceIds": self.marketplace_id,
            "includedData": "issues,identifiers",
            "mode": mode
        }
        
        headers = {
            "x-amz-access-token": access_token,
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        
        try:
            response = requests.put(url, params=params, json=product_data, headers=headers)
            
            # Update rate limit tracking - handle float values
            if 'x-amzn-RateLimit-Limit' in response.headers:
                try:
                    rate_limit = response.headers['x-amzn-RateLimit-Limit']
                    # Handle cases like '5.0' by converting to float first, then int
                    self.rate_limit_remaining = int(float(rate_limit.split('/')[0]))
                except (ValueError, IndexError) as e:
                    print(f"Warning: Could not parse rate limit header: {e}")
                    self.rate_limit_remaining = 5  # Default to conservative value
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            error_data = e.response.json()
            print(f"Error creating listing for {sku}: {error_data}")
            raise

    def validate_listing(self, product_data, sku):
        """Validate a listing before submission"""
        return self.create_listing(product_data, sku, mode='VALIDATION_PREVIEW')

    def submit_listing(self, product_data, sku):
        """Submit a listing for processing"""
        return self.create_listing(product_data, sku, mode='DEFAULT')

    def get_listing(self, sku):
        """Get listing details for a specific SKU"""
        self.check_rate_limit()
        
        access_token = self.get_access_token()
        seller_id = os.getenv('SP_API_SELLER_ID')
        
        url = f"{self.base_url}/listings/2021-08-01/items/{seller_id}/{sku}"
        params = {
            "marketplaceIds": self.marketplace_id,
            "includedData": "summaries,issues,identifiers"
        }
        
        headers = {
            "x-amz-access-token": access_token,
            "accept": "application/json"
        }
        
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

if __name__ == '__main__':
    manager = SPAPIListingManager()
    
    try:
        products = manager.load_products()
        print("Products loaded successfully")
        
        # First validate all products
        print("Validating products...")
        for product in products:
            print(f"Validating product {product['sku']}...")
            validation_result = manager.validate_listing(product['product_data'], product['sku'])
            print(f"Validation for {product['sku']}: {validation_result['status']}")
            
    except json.JSONDecodeError as e:
        print(f"Error parsing products.json: {str(e)}")
    except FileNotFoundError:
        print("Error: products.json file not found")
    except Exception as e:
        print(f"Error in listing process: {str(e)}")
        import traceback
        traceback.print_exc()