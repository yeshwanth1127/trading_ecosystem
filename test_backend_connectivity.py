import asyncio
import httpx
import json

async def test_backend_connectivity():
    """Test if the backend is accessible and working"""
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Check if backend is running
            print("1. Testing backend connectivity...")
            try:
                response = await client.get("http://localhost:8000/health")
                print(f"✅ Backend is running! Status: {response.status_code}")
                print(f"Response: {response.text}")
            except httpx.ConnectError:
                print("❌ Backend is not running or not accessible")
                print("Make sure to run: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
                return
            except Exception as e:
                print(f"❌ Error connecting to backend: {e}")
                return

            # Test 2: Check if auth endpoint exists
            print("\n2. Testing auth endpoint...")
            try:
                response = await client.get("http://localhost:8000/api/v1/auth/login")
                # This should return 405 Method Not Allowed (GET not allowed on POST endpoint)
                print(f"Auth endpoint exists! Status: {response.status_code}")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 405:
                    print("✅ Auth endpoint exists (GET not allowed, which is correct)")
                else:
                    print(f"❌ Auth endpoint error: {e.response.status_code}")

            # Test 3: Test login with invalid data (should return validation error)
            print("\n3. Testing login with invalid data...")
            try:
                response = await client.post(
                    "http://localhost:8000/api/v1/auth/login",
                    json={"invalid": "data"},
                    headers={"Content-Type": "application/json"}
                )
                print(f"Login endpoint response: {response.status_code}")
                print(f"Response: {response.text}")
            except Exception as e:
                print(f"❌ Login endpoint error: {e}")

            # Test 4: Test login with missing password
            print("\n4. Testing login with missing password...")
            try:
                response = await client.post(
                    "http://localhost:8000/api/v1/auth/login",
                    json={"email": "yeshwanthsh128@gmail.com"},
                    headers={"Content-Type": "application/json"}
                )
                print(f"Login with missing password: {response.status_code}")
                print(f"Response: {response.text}")
            except Exception as e:
                print(f"❌ Login test error: {e}")

            print("\n✅ Backend connectivity tests completed!")
            print("\nTo test with your actual password, run:")
            print("python test_frontend_login.py")
            print("(Make sure to update the password in the script)")

        except Exception as e:
            print(f"❌ General error: {e}")

if __name__ == "__main__":
    asyncio.run(test_backend_connectivity())
