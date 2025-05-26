import json
import os
from dotenv import load_dotenv
from sp_api.api import ListingsItems
from sp_api.base import Marketplaces, AuthorizationError, SellingApiException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from .env file"""
    load_dotenv()
    
    return {
        "marketplace": Marketplaces.UK,
        "sandbox": os.getenv('AMZ_SANDBOX', 'True').lower() == 'true',
        "seller_id": os.getenv('SELLER_ID'),
        "refresh_token": os.getenv('SANDBOX_REFRESH_TOKEN'),
        "lwa_app_id": os.getenv('SANDBOX_CLIENT_ID'),
        "lwa_client_secret": os.getenv('SANDBOX_CLIENT_SECRET')
    }

def load_products_from_json(file_path):
    """Load and validate product data"""
    try:
        with open(file_path, 'r') as f:
            products = json.load(f)
        
        if not isinstance(products, list):
            raise ValueError("Products JSON should be an array of products")
        
        for product in products:
            if 'sku' not in product or 'product_data' not in product:
                raise ValueError("Each product must contain 'sku' and 'product_data'")
            
            product_data = product['product_data']
            required_fields = ['productType', 'attributes']
            
            for field in required_fields:
                if field not in product_data:
                    raise ValueError(f"Missing required field: {field}")
                
            attrs = product_data['attributes']
            required_attrs = ['item_name', 'brand', 'manufacturer', 'standard_price']
            
            for attr in required_attrs:
                if attr not in attrs:
                    raise ValueError(f"Missing required attribute: {attr}")
        
        return products
    except Exception as e:
        logger.error(f"Failed to load products JSON: {e}")
        raise

def create_or_update_listings(api, seller_id, products, marketplace_id, is_sandbox):
    """Process product listings with proper request structure"""
    results = []
    for product in products:
        sku = product['sku']
        try:
            # Prepare the complete request body
            request_body = {
                "productType": product['product_data']['productType'],
                "attributes": product['product_data']['attributes']
            }
            
            # Add requirements for sandbox mode
            if is_sandbox:
                request_body['requirements'] = 'LISTING'
            
            response = api.put_listings_item(
                sellerId=seller_id,
                sku=sku,
                marketplaceIds=[marketplace_id],
                body=request_body,  # Correct parameter name is 'body'
                issueLocale='en_GB'
            )
            
            results.append({
                'sku': sku,
                'success': True,
                'response': response.payload
            })
            logger.info(f"Successfully processed SKU: {sku}")
            
        except SellingApiException as e:
            error_details = {
                'code': e.code,
                'message': e.message,
                'details': e.to_dict() if hasattr(e, 'to_dict') else str(e)
            }
            results.append({
                'sku': sku,
                'success': False,
                'error': error_details
            })
            logger.error(f"API Error for SKU {sku}: {error_details}")
            
        except Exception as e:
            results.append({
                'sku': sku,
                'success': False,
                'error': str(e)
            })
            logger.error(f"Processing Error for SKU {sku}: {e}")
    
    return results

def main():
    try:
        # Load configuration
        config = load_config()
        
        # Initialize API client
        api = ListingsItems(
            marketplace=config['marketplace'],
            credentials={
                'refresh_token': config['refresh_token'],
                'lwa_app_id': config['lwa_app_id'],
                'lwa_client_secret': config['lwa_client_secret'],
                'sandbox': config['sandbox']
            }
        )
        
        # Load products
        products = load_products_from_json('products.json')
        
        # Process listings
        results = create_or_update_listings(
            api,
            config['seller_id'],
            products,
            config['marketplace'].marketplace_id,
            config['sandbox']
        )
        
        # Output results
        print("\n📊 Processing Results:")
        for result in results:
            status = "✅ Success" if result['success'] else "❌ Failed"
            print(f"{status} - SKU: {result['sku']}")
            if not result['success']:
                print(f"   Error: {result['error']}")
        
        print("\nOperation completed.")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print(f"\n🛑 Critical failure: {str(e)}")

if __name__ == '__main__':
    main()