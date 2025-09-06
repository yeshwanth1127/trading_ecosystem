import asyncio
import httpx
import json
from datetime import datetime, timedelta
from jose import jwt

# JWT settings (same as in security.py)
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"

def create_test_token(user_id: str) -> str:
    """Create a test JWT token for a user"""
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def test_balance_endpoint():
    """Test the balance endpoint"""
    # Create a test token with the actual user ID from the database
    test_user_id = "1b9efe4b-5885-4ae5-a9fa-072a9a84fd1c"  # yeshwanth sh - actual user
    token = create_test_token(test_user_id)
    
    print(f"Testing with user ID: {test_user_id}")
    print(f"Token: {token[:50]}...")
    
    async with httpx.AsyncClient() as client:
        # Test the balance endpoint
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await client.get(
                "http://localhost:8000/api/v1/trading-challenges/me/balance",
                headers=headers
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Balance Data: {json.dumps(data, indent=2)}")
            elif response.status_code == 404:
                print("No active challenge found - this is expected if no data exists")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Error calling endpoint: {e}")

if __name__ == "__main__":
    asyncio.run(test_balance_endpoint())
