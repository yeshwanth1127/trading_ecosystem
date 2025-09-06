import asyncio
import httpx
import json

async def test_login():
    """Test the login endpoint to get a proper authentication token"""
    async with httpx.AsyncClient() as client:
        try:
            # Test login with the test user
            login_data = {
                "email": "test@example.com",
                "password": "testpassword123"  # This should match what was used to create the user
            }
            
            print("Testing login endpoint...")
            response = await client.post(
                "http://localhost:8000/api/v1/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                print(f"✅ Login successful! Token: {token[:50]}...")
                
                # Now test the balance endpoint with this token
                print("\nTesting balance endpoint with login token...")
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                balance_response = await client.get(
                    "http://localhost:8000/api/v1/trading-challenges/me/balance",
                    headers=headers
                )
                
                print(f"Balance Status Code: {balance_response.status_code}")
                if balance_response.status_code == 200:
                    balance_data = balance_response.json()
                    print(f"✅ Balance loaded successfully!")
                    print(f"Available Balance: ₹{balance_data.get('available_balance', 0)}")
                    print(f"Total Equity: ₹{balance_data.get('total_equity', 0)}")
                else:
                    print(f"❌ Balance request failed: {balance_response.text}")
                    
            else:
                print(f"❌ Login failed: {response.text}")
                
        except Exception as e:
            print(f"Error in login test: {e}")

if __name__ == "__main__":
    asyncio.run(test_login())
