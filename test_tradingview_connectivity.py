import asyncio
import httpx

async def test_tradingview_connectivity():
    """Test if TradingView CDN is accessible"""
    async with httpx.AsyncClient() as client:
        try:
            print("Testing TradingView CDN connectivity...")
            
            # Test TradingView CDN
            response = await client.get("https://s3.tradingview.com/tv.js", timeout=10.0)
            print(f"TradingView CDN Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ TradingView CDN is accessible")
                print(f"Content length: {len(response.content)} bytes")
            else:
                print(f"❌ TradingView CDN returned status {response.status_code}")
                
        except httpx.ConnectError:
            print("❌ Cannot connect to TradingView CDN")
        except httpx.TimeoutException:
            print("❌ TradingView CDN request timed out")
        except Exception as e:
            print(f"❌ Error testing TradingView CDN: {e}")
            
        # Test alternative CDN
        try:
            print("\nTesting alternative TradingView CDN...")
            response = await client.get("https://cdnjs.cloudflare.com/ajax/libs/tradingview/1.0.0/tv.js", timeout=10.0)
            print(f"Alternative CDN Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Alternative CDN is accessible")
            else:
                print(f"❌ Alternative CDN returned status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing alternative CDN: {e}")

if __name__ == "__main__":
    asyncio.run(test_tradingview_connectivity())
