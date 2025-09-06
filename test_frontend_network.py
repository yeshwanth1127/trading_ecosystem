import asyncio
import httpx
import socket

async def test_network_configurations():
    """Test different network configurations for frontend connectivity"""
    
    # Get local IP address
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"Your local IP address: {local_ip}")
    except Exception as e:
        print(f"Could not get local IP: {e}")
        local_ip = "127.0.0.1"
    
    # Test different URLs
    urls_to_test = [
        "http://localhost:8000",
        f"http://{local_ip}:8000",
        "http://127.0.0.1:8000",
        "http://10.0.2.2:8000",  # Android emulator
        "http://host.docker.internal:8000",  # Docker
    ]
    
    async with httpx.AsyncClient() as client:
        for url in urls_to_test:
            try:
                print(f"\nTesting: {url}")
                response = await client.get(f"{url}/health", timeout=5.0)
                if response.status_code == 200:
                    print(f"✅ {url} - SUCCESS")
                    print(f"   Response: {response.text[:100]}...")
                else:
                    print(f"❌ {url} - Status: {response.status_code}")
            except httpx.ConnectError:
                print(f"❌ {url} - Connection failed")
            except httpx.TimeoutException:
                print(f"❌ {url} - Timeout")
            except Exception as e:
                print(f"❌ {url} - Error: {e}")
    
    print(f"\n📱 For Flutter mobile app, try using: http://{local_ip}:8000")
    print("📱 For Android emulator, try using: http://10.0.2.2:8000")
    print("📱 For iOS simulator, try using: http://localhost:8000")

if __name__ == "__main__":
    asyncio.run(test_network_configurations())
