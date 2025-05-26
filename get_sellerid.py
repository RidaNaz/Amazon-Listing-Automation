import os
from dotenv import load_dotenv
from sp_api.api import Sellers
from sp_api.base import Marketplaces, SellingApiForbiddenException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize API client
        sellers_api = Sellers(
            marketplace=Marketplaces.UK,
            credentials={
                "refresh_token": os.getenv('SANDBOX_REFRESH_TOKEN'),
                "lwa_app_id": os.getenv('SANDBOX_CLIENT_ID'),
                "lwa_client_secret": os.getenv('SANDBOX_CLIENT_SECRET'),
                "sandbox": True  # Explicit sandbox mode
            }
        )
        
        # Make the API call
        response = sellers_api.get_marketplace_participation()
        print("Success! Response:", response.payload)
        
    except SellingApiForbiddenException as e:
        logger.error("Authentication failed. Possible causes:")
        logger.error("1. Invalid/expired refresh token")
        logger.error("2. Incorrect IAM role configuration")
        logger.error("3. SP-API application not authorized")
        logger.error(f"Details: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == '__main__':
    main()