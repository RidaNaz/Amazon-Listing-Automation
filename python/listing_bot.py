import json
from sp_api.api import ListingsItems
from sp_api.base import Marketplaces, AuthorizationError
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_credentials(config):
    """Print credential information (redact secrets in production)"""
    print("\n🔍 Configuration Debug:")
    print(f"Marketplace: {config['marketplace']}")
    print(f"Seller ID: {config['seller_id']}")
    print(f"LWA App ID: {config['lwa_app_id']}")
    print(f"Sandbox Mode: {config['sandbox']}")
    print("Refresh Token:", "*****" + config['refresh_token'][-4:] if config['refresh_token'] else "MISSING")
    print("Client Secret:", "*****" + config['lwa_client_secret'][-4:] if config['lwa_client_secret'] else "MISSING")

def main():
    # Update these with your actual credentials
    config = {
          "marketplace": Marketplaces.UK,  # Add this import at top: from sp_api.base import Marketplaces
          "sandbox": True,  # Set False for production
          'seller_id': 'A1JCZW9YA2XDCG',  # 12-char fake ID (sandbox only)
          "refresh_token": "Atzr|IwEBICFycc-9WLwEw4N7hXQScOtzWBNXohwq_lfoI8x7pLS67HChpY6EEwxjlYNJalIwFzl38wuCKw_-j0VzQLc0Cjw7d1_Dx60Nu3IPOOFwy-0TKjBN-CHtfSsVfPnD2JZ9eQoXUmzuNz8eP-eUSLtBjHxpJac3H05fNXujP2kx-XjoaYrLkOMakQ09yZss_OBYyP1HY-_4JG-b7yxy6GuORIVcnx3wns8WyrNQL3tYx71yN-iJCFasx07c7qogztTEO6EwIUV9zaxqJmwxRKiRWf05N-MEFexgDrAYuDA-GycI4tQNSHGk7yhpZuOPodlDtEV4SldGaL86nDKoBkryjX40",
          "lwa_app_id": "amzn1.application-oa2-client.66d2269ea5344f11990b1f0df044e540",
          "lwa_client_secret": "amzn1.oa2-cs.v1.92f7c818bc2458e6e29688c3dea9968be1f6a3294fa693929c3771da16f8c1d8",
        }
    
    debug_credentials(config)
    
    try:
        api = ListingsItems(
            marketplace=config['marketplace'],
            credentials={
                'refresh_token': config['refresh_token'],
                'lwa_app_id': config['lwa_app_id'],
                'lwa_client_secret': config['lwa_client_secret'],
                'sandbox': config['sandbox']
            }
        )
        
        # Simple test request
        response = api.get_listings_item(
            sellerId=config['seller_id'],
            sku='TEST_SAMPLE',
            marketplaceIds=[config['marketplace'].marketplace_id]
        )
        
        print("\n✅ Success! API Response:", response)
        
    except AuthorizationError as e:
        print("\n❌ Authentication Failed!")
        print("Error:", e)
        print("\nTroubleshooting Steps:")
        print("1. Verify all credentials are correct")
        print("2. Ensure sandbox/production environment matches")
        print("3. Check refresh token hasn't expired")
        print("4. Validate IAM role permissions")
    except Exception as e:
        print("\n⚠️ Unexpected Error:", e)

if __name__ == '__main__':
    main()