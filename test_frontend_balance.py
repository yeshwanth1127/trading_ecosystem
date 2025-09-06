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

async def test_frontend_balance_flow():
    """Test the complete frontend balance loading flow"""
    # Use the actual user ID from the database
    test_user_id = "69a7b340-8106-4577-8bd4-de9fe02f5cd6"  # Test User from database
    token = create_test_token(test_user_id)

    print(f"Testing frontend balance flow with user ID: {test_user_id}")
    print(f"Token: {token[:50]}...")

    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            # Test 1: Get active challenge selection (same as account details screen)
            print("\n1. Testing active challenge selection endpoint...")
            response1 = await client.get(
                "http://localhost:8000/api/v1/challenges/selections/me/active",
                headers=headers
            )
            
            print(f"Status Code: {response1.status_code}")
            if response1.status_code == 200:
                data1 = response1.json()
                print(f"Challenge Selection Data: {json.dumps(data1, indent=2)}")
                
                # Extract amount from challenge selection
                amount_str = data1.get('amount', '0')
                print(f"Amount from challenge selection: {amount_str}")
                
                # Convert to number (same logic as backend)
                cleaned_amount = amount_str.replace('₹', '').replace(',', '').replace(' ', '')
                amount_value = float(cleaned_amount)
                print(f"Converted amount: {amount_value}")
            else:
                print(f"Error: {response1.text}")

            # Test 2: Get balance endpoint (what frontend calls)
            print("\n2. Testing balance endpoint...")
            response2 = await client.get(
                "http://localhost:8000/api/v1/trading-challenges/me/balance",
                headers=headers
            )
            
            print(f"Status Code: {response2.status_code}")
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"Balance Data: {json.dumps(data2, indent=2)}")
                
                # Check if the balance matches the challenge selection amount
                available_balance = data2.get('available_balance', 0.0)
                print(f"Available Balance: {available_balance}")
                
                if available_balance == amount_value:
                    print("✅ SUCCESS: Balance matches challenge selection amount!")
                else:
                    print(f"❌ MISMATCH: Balance ({available_balance}) != Amount ({amount_value})")
            else:
                print(f"Error: {response2.text}")

        except Exception as e:
            print(f"Error in frontend balance flow: {e}")

if __name__ == "__main__":
    asyncio.run(test_frontend_balance_flow())
