import requests
import json
import os
import time
import logging
from dotenv import load_dotenv
from typing import List, Dict, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AmazonSPAPI:
    def __init__(self):
        self.marketplace_id = "A1F83G8C2ARO7P"  # UK marketplace
        self.seller_id = os.getenv('SELLER_ID')
        self.base_url = "https://sellingpartnerapi-eu.amazon.com"
        self.rate_limit_delay = 0.2  # Delay between requests (seconds)
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def get_access_token(self) -> str:
        """Get LWA access token using refresh token"""
        token_url = "https://api.amazon.com/auth/o2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": os.getenv('SP_API_REFRESH_TOKEN'),
            "client_id": os.getenv('SP_API_CLIENT_ID'),
            "client_secret": os.getenv('SP_API_CLIENT_SECRET')
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            return response.json()['access_token']
        except Exception as e:
            logger.error(f"Failed to get access token: {str(e)}")
            raise

    def validate_price(self, price_data):
        """Validate price meets Amazon's requirements"""
        if not isinstance(price_data, dict):
            return False
        if 'amount' not in price_data or 'currency' not in price_data:
            return False
        try:
            float(price_data['amount'])
        except ValueError:
            return False
        return True

    def load_products(self, file_path='products.json'):
        """Load products from JSON file and adapt for sandbox"""
        with open(file_path) as f:
            products = json.load(f)
        
        # Sandbox-specific modifications
        for product in products:
            product['product_data']['requirements'] = 'LISTING'
            product['product_data']['attributes']['brand'] = 'SANDBOX_BRAND'
            product['product_data']['attributes']['manufacturer'] = 'SANDBOX_MFG'

            # Fix price formatting
            if 'standard_price' in product['product_data']['attributes']:
                price = product['product_data']['attributes']['standard_price']
                if 'value' in price:  # Convert from value/currency to amount/currency
                    product['product_data']['attributes']['standard_price'] = {
                        'amount': price['value'],
                        'currency': price.get('currency', 'GBP')
                    }

                if not self.validate_price(product['product_data']['attributes'].get('standard_price')):
                    logger.error(f"Invalid price format for SKU {product['sku']}")
                    
                elif 'amount' not in price:
                    product['product_data']['attributes']['standard_price'] = {
                        'amount': 19.99,  # Default sandbox price
                        'currency': 'GBP'
                    }

            # Ensure main image exists
            product['product_data']['attributes']['main_image'] = {
                "link": "https://www.junglemug.com/cdn/shop/collections/Group_39892_5c108ecf-6033-4f13-934a-e6635d670c72.png?v=1737468874",
                "height": 500,
                "width": 500
            }
            
            # Ensure required fields for sandbox
            if product['product_data']['productType'] == 'SHOES':
                product['product_data']['attributes'].setdefault('size', '10')
            elif product['product_data']['productType'] == 'LUGGAGE':
                product['product_data']['attributes'].setdefault('size', 'Medium')
                
        return products

    def _prepare_listing_payload(self, product: Dict) -> Dict:
        """Prepare the listing payload according to Amazon's requirements"""
        payload = {
            "productType": product['product_data'].get('productType', 'HOME'),
            "requirements": product['product_data'].get('requirements', 'LISTING'),
            "attributes": product['product_data'].get('attributes', {})
        }
        
        # Ensure price is properly formatted
        if 'attributes' in payload:
            if 'price' in payload['attributes']:
                # Convert simple price to Amazon's format
                price = payload['attributes'].pop('price')
                payload['attributes']['standard_price'] = {
                    'value': float(price),
                    'currency': 'GBP'  # Adjust based on your marketplace
                }
        
        return payload

    def create_listing(self, product: Dict, mode: str = None) -> Dict:
        """Create or update a single listing"""
        self._rate_limit()
        access_token = self.get_access_token()
        url = f"{self.base_url}/listings/2021-08-01/items/{self.seller_id}/{product['sku']}"
        
        params = {
            "marketplaceIds": self.marketplace_id,
            "includedData": "issues,identifiers"
        }
        
        if mode:
            params["mode"] = mode  # 'VALIDATION_PREVIEW' or None for actual submission
        
        headers = {
            "x-amz-access-token": access_token,
            "Content-Type": "application/json",
            "accept": "application/json",
            "User-Agent": "MyAmazonIntegration/1.0"
        }
        
        payload = self._prepare_listing_payload(product)
        
        try:
            logger.info(f"Submitting listing for SKU: {product['sku']}")
            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            response = requests.put(url, params=params, json=payload, headers=headers)
            response_data = response.json()
            
            # Log the full response in debug mode
            logger.debug(f"API Response: {json.dumps(response_data, indent=2)}")
            
            if response.status_code != 200:
                logger.error(f"API Error Response: {response.text}")
                response.raise_for_status()
            
            # Check the submission status in the response
            if response_data.get('status') == 'INVALID':
                logger.warning(f"Listing submission invalid for SKU {product['sku']}")
                for issue in response_data.get('issues', []):
                    logger.warning(f"Issue: {issue.get('code')} - {issue.get('message')}")
            
            return {
                'sku': product['sku'],
                'status': response_data.get('status', 'UNKNOWN'),
                'response': response_data,
                'success': response_data.get('status') in ['ACCEPTED', 'VALID']
            }
            
        except Exception as e:
            logger.error(f"Failed to create listing for SKU {product['sku']}: {str(e)}")
            return {
                'sku': product['sku'],
                'status': 'FAILED',
                'error': str(e),
                'success': False
            }

    def create_listings(self, mode: str = None) -> List[Dict]:
        """Create listings for all products in JSON file"""
        products = self.load_products()
        results = []
        
        for product in products:
            result = self.create_listing(product, mode)
            results.append(result)
            
            # For VALIDATION_PREVIEW mode, we might want to stop after first item
            if mode == 'VALIDATION_PREVIEW' and results:
                break
                
        return results

    def get_listing(self, sku: str) -> Dict:
        """Get listing details for a specific SKU"""
        self._rate_limit()
        access_token = self.get_access_token()
        
        url = f"{self.base_url}/listings/2021-08-01/items/{self.seller_id}/{sku}"
        params = {
            "marketplaceIds": self.marketplace_id,
            "includedData": "summaries,issues,attributes"
        }
        
        headers = {
            "x-amz-access-token": access_token,
            "accept": "application/json"
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get listing for SKU {sku}: {str(e)}")
            return {'error': str(e)}

    def get_product_type_requirements(self, product_type: str = 'HOME') -> Dict:
        """Get requirements for a specific product type"""
        self._rate_limit()
        url = f"{self.base_url}/definitions/2020-09-01/productTypes/{product_type}"
        params = {
            "marketplaceIds": self.marketplace_id
        }
        headers = {
            "x-amz-access-token": self.get_access_token()
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get requirements for product type {product_type}: {str(e)}")
            return {'error': str(e)}

if __name__ == '__main__':
    api = AmazonSPAPI()
    
    # First validate a product
    logger.info("Running validation preview...")
    validation_results = api.create_listings(mode='VALIDATION_PREVIEW')
    logger.info(f"Validation result: {validation_results[0]['status']}")
    
    if validation_results[0]['success']:
        # If validation passes, create the listings
        logger.info("Validation successful. Creating listings...")
        creation_results = api.create_listings()
        
        logger.info("Creation Results:")
        for result in creation_results:
            status = "SUCCESS" if result['success'] else "FAILED"
            logger.info(f"SKU: {result['sku']} - {status}")
            if 'response' in result:
                logger.debug(json.dumps(result['response'], indent=2))
            elif 'error' in result:
                logger.error(f"Error: {result['error']}")
        
        # Check one listing as example
        if creation_results:
            sample_sku = creation_results[0]['sku']
            logger.info(f"\nGetting listing details for {sample_sku}:")
            listing_details = api.get_listing(sample_sku)
            logger.info(json.dumps(listing_details, indent=2))
    else:
        logger.error("Validation failed. Not proceeding with listing creation.")
        logger.error(json.dumps(validation_results[0], indent=2))