import asyncio
import httpx
import json
import getpass

async def test_login_with_password():
    """Test login with the actual user password"""
    async with httpx.AsyncClient() as client:
        try:
            # Get password from user input (hidden)
            print("Testing login for: yeshwanthsh128@gmail.com")
            password = getpass.getpass("Enter your password: ")
            
            login_data = {
                "email": "yeshwanthsh128@gmail.com",
                "password": password
            }
            
            print("Testing login...")
            response = await client.post(
                "http://localhost:8000/api/v1/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                user_id = data.get('user', {}).get('user_id')
                print(f"✅ Login successful!")
                print(f"User ID: {user_id}")
                print(f"Token: {token[:50]}...")
                
                # Test balance endpoint
                print("\nTesting balance endpoint...")
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                balance_response = await client.get(
                    "http://localhost:8000/api/v1/trading-challenges/me/balance",
                    headers=headers
                )
                
                print(f"Balance Status: {balance_response.status_code}")
                if balance_response.status_code == 200:
                    balance_data = balance_response.json()
                    print(f"✅ Balance loaded successfully!")
                    print(f"Available Balance: ₹{balance_data.get('available_balance', 0):,.2f}")
                    print(f"Total Equity: ₹{balance_data.get('total_equity', 0):,.2f}")
                    print(f"Challenge ID: {balance_data.get('challenge_id')}")
                    print(f"Status: {balance_data.get('status')}")
                else:
                    print(f"❌ Balance request failed: {balance_response.text}")
                    
            elif response.status_code == 401:
                print("❌ Login failed: Incorrect email or password")
                print("Please check your password and try again")
            elif response.status_code == 422:
                print("❌ Login failed: Validation error")
                print(f"Response: {response.text}")
            else:
                print(f"❌ Login failed with status {response.status_code}: {response.text}")
                
        except httpx.ConnectError:
            print("❌ Connection error: Cannot connect to http://localhost:8000")
            print("Make sure the backend server is running")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_login_with_password())
