from sp_api.base import AccessTokenClient
# from sp_api.base.credential_provider import CredentialProvider, Credentials
import logging

# Set up logging to see detailed output
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_authentication():
    """Test SP-API authentication with your credentials"""
    try:
        # Create proper Credentials object (not dict)
        credentials = dict(
            refresh_token='Atzr|IwEBICFycc-9WLwEw4N7hXQScOtzWBNXohwq_lfoI8x7pLS67HChpY6EEwxjlYNJalIwFzl38wuCKw_-j0VzQLc0Cjw7d1_Dx60Nu3IPOOFwy-0TKjBN-CHtfSsVfPnD2JZ9eQoXUmzuNz8eP-eUSLtBjHxpJac3H05fNXujP2kx-XjoaYrLkOMakQ09yZss_OBYyP1HY-_4JG-b7yxy6GuORIVcnx3wns8WyrNQL3tYx71yN-iJCFasx07c7qogztTEO6EwIUV9zaxqJmwxRKiRWf05N-MEFexgDrAYuDA-GycI4tQNSHGk7yhpZuOPodlDtEV4SldGaL86nDKoBkryjX40',
            lwa_app_id='amzn1.sp.solution.035d94ae-33b5-47d3-b855-9475e61c3c5b',
            lwa_client_secret='amzn1.oa2-cs.v1.2cd2f244b0167a2de88309aa10d912de070c0e0406f4613a4334f59da436de95',
            aws_secret_key=None,
            aws_access_key=None,
            role_arn=None
        )
        
        # Initialize client (sandbox flag is now properly handled)
        token_client = AccessTokenClient(credentials=credentials)
        
        # Get auth token
        token = token_client.get_auth()
        
        print("\n✅ Authentication Successful!")
        print(f"Access Token: {token.access_token[:15]}...")
        print(f"Expires in: {token.expires_in} seconds")
        return True
        
    except Exception as e:
        print("\n❌ Authentication Failed:")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Details: {str(e)}")
        
        # Additional troubleshooting info
        print("\n🔧 Troubleshooting Tips:")
        if "invalid_client" in str(e):
            print("- Verify your LWA Client ID and Secret are correct")
            print("- Check your refresh token is valid and not expired")
        elif "unauthorized_client" in str(e):
            print("- Ensure your application is authorized in Seller Central")
            print("- Check IAM role permissions")
        else:
            print("- Verify all credentials are correctly entered")
            print("- Check sandbox/production environment matches")
        
        return False

if __name__ == '__main__':
    print("Testing Amazon SP-API Authentication...")
    test_authentication()