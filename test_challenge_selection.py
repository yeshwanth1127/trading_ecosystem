import asyncio
import httpx
import json
from datetime import datetime, timedelta
import jwt

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

async def test_challenge_selection_endpoint():
    """Test the challenge selection endpoint (same as account details screen)"""
    # Create a test token with a sample user ID
    test_user_id = "550e8400-e29b-41d4-a716-446655440000"  # Sample UUID
    token = create_test_token(test_user_id)

    print(f"Testing with user ID: {test_user_id}")
    print(f"Token: {token[:50]}...")

    async with httpx.AsyncClient() as client:
        # Test the challenge selection endpoint (same as account details screen)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            response = await client.get(
                "http://localhost:8000/api/v1/challenges/selections/me/active",
                headers=headers
            )

            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")

            if response.status_code == 200:
                data = response.json()
                print(f"Challenge Selection Data: {json.dumps(data, indent=2)}")
                
                # Extract and convert amount
                if 'amount' in data:
                    amount_str = data['amount']
                    print(f"Amount from response: {amount_str}")
                    
                    # Convert to number
                    cleaned_amount = amount_str.replace('₹', '').replace(',', '').replace(' ', '')
                    amount_value = float(cleaned_amount)
                    print(f"Converted amount: {amount_value}")
                    
            elif response.status_code == 404:
                print("No active challenge selection found - this is expected if no data exists")
            else:
                print(f"Error: {response.text}")

        except Exception as e:
            print(f"Error calling endpoint: {e}")

if __name__ == "__main__":
    asyncio.run(test_challenge_selection_endpoint())
