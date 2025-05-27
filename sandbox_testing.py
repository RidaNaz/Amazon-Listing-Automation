import requests
import json
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SPAPI:
    def __init__(self):
        self.access_token = None
        self.token_expiry = None
        self.refresh_token = os.getenv('SANDBOX_REFRESH_TOKEN')
        self.client_id = os.getenv('SANDBOX_CLIENT_ID')
        self.client_secret = os.getenv('SANDBOX_CLIENT_SECRET')
        self.marketplace_id = os.getenv('UK_MARKETPLACE_ID', 'A1F83G8C2ARO7P')
        
    def get_access_token(self, force_refresh=False):
        """Get valid access token with automatic refresh"""
        if not force_refresh and self.access_token and self.token_expiry and time.time() < self.token_expiry:
            return self.access_token
            
        token_url = "https://api.amazon.com/auth/o2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(token_url, data=data, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data['access_token']
            # Set expiry 5 minutes before actual expiry to be safe
            self.token_expiry = time.time() + token_data['expires_in'] - 300
            
            print("Successfully refreshed access token")
            return self.access_token
            
        except Exception as e:
            print(f"Failed to refresh access token: {str(e)}")
            raise ValueError("Could not obtain valid access token")

    def make_request(self, method, url, **kwargs):
        """Make authenticated API request with automatic token refresh"""
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                if not self.access_token or time.time() >= self.token_expiry:
                    self.get_access_token()
                
                headers = kwargs.get('headers', {})
                headers.update({
                    "x-amz-access-token": self.access_token,
                    "accept": "application/json"
                })
                kwargs['headers'] = headers
                
                response = requests.request(method, url, **kwargs)
                
                # If unauthorized, try refreshing token once
                if response.status_code == 403 and attempt < max_retries:
                    error_data = response.json()
                    if any(error.get('code') == 'Unauthorized' for error in error_data.get('errors', [])):
                        print("Access token expired, refreshing...")
                        self.get_access_token(force_refresh=True)
                        continue
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries:
                    raise
                time.sleep(1)
        
        raise Exception("Max retries exceeded")

def load_products(file_path='products.json'):
    """Load products with proper schema validation"""
    with open(file_path) as f:
        products = json.load(f)
    
    TEST_IMAGES = {
        'LUGGAGE': 'https://m.media-amazon.com/images/I/71O+j4G4RBL._AC_UL1500_.jpg',
        'SHOES': 'https://m.media-amazon.com/images/I/71hUzQKBt+L._AC_UL1500_.jpg'
    }

    for product in products:
        product_type = product['product_data']['productType']
        product['product_data']['requirements'] = 'LISTING'
        
        # Standardize attributes
        attrs = product['product_data']['attributes']
        attrs.update({
            'brand': 'GenericBrand',
            'manufacturer': 'GenericManufacturer',
            'item_name': attrs.get('item_name', f"Test {product_type}"),
            'external_product_id': f"TEST{product['sku']}",
            'external_product_id_type': 'GTIN',
            'product_description': 'Test product for sandbox environment'
        })

        # Product-specific attributes
        if product_type == 'LUGGAGE':
            attrs.update({
                'size': {'value': '55x35x20', 'unit': 'cm'},
                'color': 'Black',
                'material': 'Polycarbonate',
                'closure_type': 'Zipper'
            })
        elif product_type == 'SHOES':
            attrs.update({
                'size': {'value': '10', 'unit': 'UK'},
                'color': 'Black',
                'model': 'RunnerPro',
                'shoe_width': 'Medium'
            })

        # Ensure proper pricing
        if 'standard_price' in attrs:
            std_price = attrs['standard_price']['value']
            attrs['minimum_price'] = {
                'value': round(std_price * 0.85, 2),
                'currency': attrs['standard_price']['currency']
            }

        # Set main image
        attrs['main_image'] = {
            'link': TEST_IMAGES.get(product_type, TEST_IMAGES['LUGGAGE']),
            'height': 1500,
            'width': 1500
        }
    
    return products

def create_listings(spapi):
    """Create listings with proper error handling"""
    products = load_products()
    results = []
    
    for product in products:
        try:
            print(f"\nCreating listing for SKU: {product['sku']}")
            print("Payload:", json.dumps(product['product_data'], indent=2))
            
            url = f"https://sandbox.sellingpartnerapi-eu.amazon.com/listings/2021-08-01/items/ATVPDKIKX0DER/{product['sku']}"
            response = spapi.make_request(
                'PUT',
                url,
                params={"marketplaceIds": spapi.marketplace_id, "includedData": "issues"},
                json=product['product_data'],
                headers={"Content-Type": "application/json"}
            )
            
            response_data = response.json()
            print("Success:", json.dumps(response_data, indent=2))
            
            results.append({
                'sku': product['sku'],
                'status': 'SUCCESS',
                'response': response_data
            })
            
        except requests.exceptions.HTTPError as e:
            error_data = e.response.json()
            error_msg = error_data.get('errors', [{}])[0].get('message', str(e))
            print(f"Error: {error_msg}")
            
            results.append({
                'sku': product['sku'],
                'status': 'API_ERROR',
                'status_code': e.response.status_code,
                'error': error_msg,
                'details': error_data
            })
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error: {error_msg}")
            
            results.append({
                'sku': product['sku'],
                'status': 'ERROR',
                'error': error_msg
            })
    
    return results

def get_listing(spapi, sku):
    """Get listing details for a specific SKU"""
    try:
        url = f"https://sandbox.sellingpartnerapi-eu.amazon.com/listings/2021-08-01/items/ATVPDKIKX0DER/{sku}"
        response = spapi.make_request(
            'GET',
            url,
            params={
                "marketplaceIds": spapi.marketplace_id,
                "includedData": "summaries,issues,offers,fulfillmentAvailability"
            }
        )
        return response.json()
    except Exception as e:
        print(f"Error getting listing for {sku}: {str(e)}")
        return None

def check_listing_quality(listing_data):
    """Check listing quality with sandbox-specific handling"""
    if not listing_data or 'error' in listing_data:
        return False, "Failed to retrieve listing data"
    
    issues = listing_data.get('issues', [])
    
    # Filter out sandbox-specific issues we can't fix
    filtered_issues = []
    for issue in issues:
        if issue.get('code') in ['18742']:  # Restricted product error
            continue  # Skip this in sandbox
        filtered_issues.append(issue)
    
    critical_errors = [issue for issue in filtered_issues if issue.get('severity') == 'ERROR']
    
    if critical_errors:
        error_messages = "\n".join(
            f"{error['code']}: {error['message']}" 
            for error in critical_errors
        )
        return False, f"Critical listing issues found:\n{error_messages}"
    
    return True, "Listing meets quality standards (sandbox-adjusted)"

def main():
    print("Starting Amazon SP-API Sandbox Listing Management")
    
    try:
        spapi = SPAPI()
        
        # Verify token works
        spapi.get_access_token()
        print("Authentication successful")
        
        # Create listings
        print("\nCreating listings...")
        results = create_listings(spapi)
        
        print("\nResults:")
        for result in results:
            status = result['status']
            if status == 'SUCCESS':
                print(f"✅ {result['sku']}: Success")
            else:
                print(f"❌ {result['sku']}: {status} - {result.get('error', '')}")
                if 'details' in result:
                    with open(f'error_{result["sku"]}.json', 'w') as f:
                        json.dump(result['details'], f, indent=2)
        
        # Validate successful listings
        successful = [r for r in results if r['status'] == 'SUCCESS']
        if successful:
            print("\nValidating listings...")
            for result in successful[:3]:  # Validate first 3 successful listings
                sku = result['sku']
                print(f"\nChecking listing quality for {sku}:")
                
                listing_data = get_listing(spapi, sku)
                if listing_data:
                    is_valid, message = check_listing_quality(listing_data)
                    print(f"\n{sku}: {'✅ Valid' if is_valid else '❌ Invalid'}")
                    print(message)
                    
                    # Save response
                    with open(f'listing_{sku}.json', 'w') as f:
                        json.dump(listing_data, f, indent=2)
                else:
                    print(f"Failed to retrieve listing data for {sku}")
        else:
            print("\nNo successful listings to validate")
            
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
    
    print("\nProcess completed")

if __name__ == '__main__':
    main()