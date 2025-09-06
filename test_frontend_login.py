import asyncio
import httpx
import json

async def test_frontend_login():
    """Test the frontend login flow with actual user credentials"""
    async with httpx.AsyncClient() as client:
        try:
            # Test login with the actual user (yeshwanth sh)
            login_data = {
                "email": "yeshwanthsh128@gmail.com",
                "password": "your_password_here"  # You need to provide the actual password
            }
            
            print("Testing frontend login endpoint...")
            print(f"URL: http://localhost:8000/api/v1/auth/login")
            print(f"Data: {login_data}")
            
            response = await client.post(
                "http://localhost:8000/api/v1/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                user_id = data.get('user', {}).get('user_id')
                print(f"✅ Login successful!")
                print(f"Token: {token[:50]}...")
                print(f"User ID: {user_id}")
                
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
                    
            elif response.status_code == 401:
                print("❌ Login failed: Incorrect email or password")
            elif response.status_code == 422:
                print("❌ Login failed: Validation error - check request format")
            else:
                print(f"❌ Login failed with status {response.status_code}: {response.text}")
                
        except httpx.ConnectError:
            print("❌ Connection error: Cannot connect to http://localhost:8000")
            print("Make sure the backend server is running on port 8000")
        except Exception as e:
            print(f"❌ Error in login test: {e}")

if __name__ == "__main__":
    asyncio.run(test_frontend_login())
