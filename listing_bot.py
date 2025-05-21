import json
from sp_api.api import ListingsItems
from sp_api.base import Marketplaces, SellingApiException
from config import CONFIG

def create_listing(product):
    try:
        listings_api = ListingsItems(
            marketplace=CONFIG['marketplace'],
            credentials={
                'refresh_token': CONFIG['refresh_token'],
                'lwa_app_id': CONFIG['lwa_app_id'],
                'lwa_client_secret': CONFIG['lwa_client_secret']
            }
        )
        
        # Correct parameter structure
        response = listings_api.put_listings_item(
            body={
                'productType': 'MUG',
                'requirements': 'LISTING',
                'attributes': {
                    'item_name': product['title'],
                    'standard_price': {
                        'value': str(product['price']),
                        'currency': 'GBP'
                    },
                    'quantity': product['quantity']
                }
            },
            sellerId=CONFIG['seller_id'],
            sku=product['sku'],
            marketplaceIds=[CONFIG['marketplace'].marketplace_id]  # Note: array of marketplace IDs
        )
        
        print(f"✅ Successfully listed {product['sku']}")
        print(f"ASIN: {response.payload['asin']}")
        return response
        
    except SellingApiException as e:
        print(f"❌ Failed to list {product['sku']}: {e.error}")
        return None

if __name__ == '__main__':
    with open('products.json') as f:
        products = json.load(f)
    
    print(f"Processing {len(products)} products...")
    for product in products:
        create_listing(product)