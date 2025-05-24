import os
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
# Get credentials from environment variables
auth_code = os.getenv('AMAZON_AUTH_CODE')
client_id = os.getenv('AMAZON_CLIENT_ID')
client_secret = os.getenv('AMAZON_CLIENT_SECRET')
redirect_uri = os.getenv('AMAZON_REDIRECT_URI')

def get_refresh_token() -> Optional[str]:
    """
    Fetches a new refresh token from Amazon OAuth 2.0 endpoint
    Returns:
        str: Refresh token (starts with 'Atzr|...')
    """
    if not all([auth_code, client_id, client_secret, redirect_uri]):
        print("Error: Missing required environment variables")
        return None

    url = "https://api.amazon.com/auth/o2/token"
    
    payload = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        
        refresh_token = response.json().get('refresh_token')
        if refresh_token:
            print("Successfully obtained refresh token")
            return refresh_token
        else:
            print("Error: No refresh token in response")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

if __name__ == "__main__":
    token = get_refresh_token()
    if token:
        # Example: Store in new .env file or secrets manager
        with open('.refresh_token', 'w') as f:
            f.write(f"AMAZON_REFRESH_TOKEN={token}")
        print("Refresh token saved securely")