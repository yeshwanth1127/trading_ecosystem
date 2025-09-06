import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from app.config.settings import settings
from app.services.silent_market_data_service import silent_market_data_service

logger = logging.getLogger(__name__)

class MarketDataService:
    """Service for fetching live market data from various sources"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Any] = {}
        self.cache_expiry: Dict[str, datetime] = {}
        self.cache_duration = timedelta(minutes=1)  # Cache for 1 minute
        
        # Popular crypto symbols for INR pairs
        self.crypto_symbols = [
            'BTCINR', 'ETHINR', 'BNBINR', 'ADAINR', 'SOLINR', 'XRPINR', 'DOTINR', 'DOGEINR',
            'AVAXINR', 'MATICINR', 'LINKINR', 'UNIINR', 'LTCINR', 'BCHINR', 'XLMINR', 'ATOMINR',
            'FTMINR', 'NEARINR', 'ALGOINR', 'VETINR', 'ICPINR', 'FILINR', 'TRXINR', 'ETCINR',
            'XMRINR', 'EOSINR', 'AAVEINR', 'SUSHIINR', 'COMPINR', 'MKRINR', 'YFIINR', 'CRVINR'
        ]
        
        # Popular stock symbols
        self.stock_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
            'JPM', 'JNJ', 'V', 'PG', 'HD', 'DIS', 'PYPL', 'ADBE',
            'CRM', 'INTC', 'VZ', 'CMCSA', 'PFE', 'TMO', 'ABT', 'KO',
            'PEP', 'WMT', 'COST', 'TXN', 'QCOM', 'AVGO', 'HON', 'LOW'
        ]

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with proper lifecycle management"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=10, connect=5, sock_read=5)
            connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=30,  # Per-host connection limit
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
            )
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={'User-Agent': 'TradingEcosystem/1.0'}
            )
        return self.session

    async def close_session(self):
        """Close aiohttp session with proper cleanup"""
        if self.session and not self.session.closed:
            try:
                await self.session.close()
                # Wait for connector to close
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error closing aiohttp session: {e}")
            finally:
                self.session = None

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache or key not in self.cache_expiry:
            return False
        return datetime.now() < self.cache_expiry[key]

    def _update_cache(self, key: str, data: Any):
        """Update cache with new data"""
        self.cache[key] = data
        self.cache_expiry[key] = datetime.now() + self.cache_duration

    async def cleanup(self):
        """Cleanup resources"""
        await self.close_session()
        self.cache.clear()
        self.cache_expiry.clear()

    async def fetch_tradingview_data(self, market_type: str) -> List[Dict[str, Any]]:
        """Fetch data from TradingView scanner"""
        try:
            session = await self.get_session()
            
            if market_type == 'crypto':
                url = 'https://scanner.tradingview.com/crypto/scan'
                symbols = [f'CRYPTO:{symbol}' for symbol in self.crypto_symbols]
            elif market_type == 'stock':
                url = 'https://scanner.tradingview.com/america/scan'
                symbols = [f'NASDAQ:{symbol}' for symbol in self.stock_symbols]
            else:
                return []

            payload = {
                "symbols": {
                    "tickers": symbols,
                    "query": {"types": []}
                },
                "columns": [
                    "symbol", "name", "price", "change", "change_abs",
                    "volume", "market_cap_basic", "price_52_week_high", "price_52_week_low"
                ],
                "range": [0, 100],
                "sort": {"sortBy": "volume", "sortOrder": "desc"}
            }

            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('data', [])
                    
                    return [
                        {
                            'symbol': item[0].replace(f'{market_type.upper()}:', ''),
                            'name': item[1],
                            'current_price': float(item[2]),
                            'price_change_24h': float(item[3]),
                            'price_change_abs_24h': float(item[4]),
                            'volume': float(item[5]),
                            'market_cap': float(item[6]),
                            'high_52w': float(item[7]),
                            'low_52w': float(item[8]),
                            'type': market_type,
                            'tv_symbol': item[0],
                            'last_updated': datetime.now().isoformat()
                        }
                        for item in results
                    ]
                else:
                    logger.warning(f"TradingView API returned status {response.status}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching TradingView {market_type} data: {e}")
            return []

    async def fetch_coingecko_data(self) -> List[Dict[str, Any]]:
        """Fetch crypto data from CoinGecko API with INR prices"""
        try:
            session = await self.get_session()
            
            # Get top 50 coins by market cap with INR prices
            url = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=inr&order=market_cap_desc&per_page=50&page=1&sparkline=false&locale=en'
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    results = []
                    for item in data:
                        try:
                            results.append({
                                'symbol': item['symbol'].upper(),
                                'name': item['name'],
                                'current_price': float(item.get('current_price', 0)),
                                'price_change_24h': float(item.get('price_change_percentage_24h', 0)),
                                'price_change_abs_24h': float(item.get('price_change_24h', 0)),
                                'volume': float(item.get('total_volume', 0)),
                                'market_cap': float(item.get('market_cap', 0)),
                                'high_52w': float(item.get('ath', 0)),
                                'low_52w': float(item.get('atl', 0)),
                                'type': 'crypto',
                                'tv_symbol': f'BINANCE:{item["symbol"].upper()}INR',
                                'last_updated': datetime.now().isoformat()
                            })
                        except (KeyError, ValueError, TypeError) as e:
                            continue
                    
                    return results
                else:
                    return []

        except Exception as e:
            return []

    async def fetch_alpha_vantage_data(self) -> List[Dict[str, Any]]:
        """Fetch Indian stock data with multiple fallback options"""
        try:
            session = await self.get_session()
            
            # Try multiple Yahoo Finance endpoints
            urls = [
                'https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?formatted=true&lang=en-US&region=IN&scrIds=most_actives&count=50&start=0',
                'https://query2.finance.yahoo.com/v1/finance/screener/predefined/saved?formatted=true&lang=en-US&region=IN&scrIds=most_actives&count=50&start=0',
                'https://query1.finance.yahoo.com/v7/finance/quote?symbols=RELIANCE.NS,TCS.NS,HDFCBANK.NS,INFY.NS,HINDUNILVR.NS,ITC.NS,SBIN.NS,BHARTIARTL.NS,KOTAKBANK.NS,LT.NS'
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin'
            }
            
            for i, url in enumerate(urls):
                try:
                    async with session.get(url, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            results = []
                            
                            if i < 2:  # Screener endpoints
                                quotes = data.get('finance', {}).get('result', [{}])[0].get('quotes', [])
                                for quote in quotes[:20]:
                                    result = self._parse_yahoo_quote(quote)
                                    if result:
                                        results.append(result)
                            else:  # Quote endpoint
                                quotes = data.get('quoteResponse', {}).get('result', [])
                                for quote in quotes[:20]:
                                    result = self._parse_yahoo_quote_v2(quote)
                                    if result:
                                        results.append(result)
                            
                            if results:
                                return results
                            
                except Exception as e:
                    continue
            
            # If all Yahoo Finance endpoints fail, try alternative approach
            return await self._fetch_indian_stocks_alternative()
            
        except Exception as e:
            return self._get_fallback_indian_stock_data()
    
    def _parse_yahoo_quote(self, quote: dict) -> dict:
        """Parse Yahoo Finance screener quote"""
        try:
            symbol = quote.get('symbol', '')
            name = quote.get('longName', symbol)
            
            # Handle nested price data structure
            price_data = quote.get('regularMarketPrice', 0)
            change_data = quote.get('regularMarketChangePercent', 0)
            change_abs_data = quote.get('regularMarketChange', 0)
            volume_data = quote.get('regularMarketVolume', 0)
            market_cap_data = quote.get('marketCap', 0)
            
            # Extract actual values from nested structure
            price = float(price_data.get('raw', 0)) if isinstance(price_data, dict) else float(price_data)
            change_percent = float(change_data.get('raw', 0)) if isinstance(change_data, dict) else float(change_data)
            change_abs = float(change_abs_data.get('raw', 0)) if isinstance(change_abs_data, dict) else float(change_abs_data)
            volume = float(volume_data.get('raw', 0)) if isinstance(volume_data, dict) else float(volume_data)
            market_cap = float(market_cap_data.get('raw', 0)) if isinstance(market_cap_data, dict) else float(market_cap_data)
            
            if price > 0:
                return {
                    'symbol': symbol,
                    'name': name,
                    'current_price': price,
                    'price_change_24h': change_percent,
                    'price_change_abs_24h': change_abs,
                    'volume': volume,
                    'market_cap': market_cap,
                    'high_52w': price * 1.2,
                    'low_52w': price * 0.8,
                    'type': 'stock',
                    'tv_symbol': f'NSE:{symbol}',
                    'last_updated': datetime.now().isoformat()
                }
        except Exception as e:
            pass
        return None
    
    def _parse_yahoo_quote_v2(self, quote: dict) -> dict:
        """Parse Yahoo Finance quote endpoint response"""
        try:
            symbol = quote.get('symbol', '')
            name = quote.get('longName', symbol)
            price = float(quote.get('regularMarketPrice', 0))
            change_percent = float(quote.get('regularMarketChangePercent', 0))
            change_abs = float(quote.get('regularMarketChange', 0))
            volume = float(quote.get('regularMarketVolume', 0))
            market_cap = float(quote.get('marketCap', 0))
            
            if price > 0:
                return {
                    'symbol': symbol,
                    'name': name,
                    'current_price': price,
                    'price_change_24h': change_percent,
                    'price_change_abs_24h': change_abs,
                    'volume': volume,
                    'market_cap': market_cap,
                    'high_52w': price * 1.2,
                    'low_52w': price * 0.8,
                    'type': 'stock',
                    'tv_symbol': f'NSE:{symbol}',
                    'last_updated': datetime.now().isoformat()
                }
        except Exception as e:
            pass
        return None
    
    async def _fetch_indian_stocks_alternative(self) -> List[Dict[str, Any]]:
        """Alternative method to fetch Indian stock data"""
        try:
            # Use a different approach - fetch individual stocks
            symbols = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'HINDUNILVR.NS']
            session = await self.get_session()
            results = []
            
            for symbol in symbols:
                try:
                    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    
                    async with session.get(url, headers=headers, timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            result = data.get('chart', {}).get('result', [{}])[0]
                            meta = result.get('meta', {})
                            
                            if meta.get('regularMarketPrice', 0) > 0:
                                results.append({
                                    'symbol': symbol,
                                    'name': meta.get('longName', symbol),
                                    'current_price': float(meta.get('regularMarketPrice', 0)),
                                    'price_change_24h': float(meta.get('regularMarketChangePercent', 0)),
                                    'price_change_abs_24h': float(meta.get('regularMarketChange', 0)),
                                    'volume': float(meta.get('regularMarketVolume', 0)),
                                    'market_cap': float(meta.get('marketCap', 0)),
                                    'high_52w': float(meta.get('fiftyTwoWeekHigh', 0)),
                                    'low_52w': float(meta.get('fiftyTwoWeekLow', 0)),
                                    'type': 'stock',
                                    'tv_symbol': f'NSE:{symbol.replace(".NS", "")}',
                                    'last_updated': datetime.now().isoformat()
                                })
                except Exception as e:
                    continue
            
            if results:
                return results
            else:
                return self._get_fallback_indian_stock_data()

        except Exception as e:
            return self._get_fallback_indian_stock_data()
    
    async def _fetch_coingecko_fallback(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch real-time crypto data from multiple sources as fallback"""
        # Try CoinGecko first
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                # Try direct symbol lookup
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd&include_24hr_change=true"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if symbol.lower() in data:
                            price_data = data[symbol.lower()]
                            return {
                                "symbol": symbol,
                                "current_price": price_data.get("usd", 0),
                                "price_change_24h": price_data.get("usd_24h_change", 0),
                                "last_updated": datetime.now().isoformat()
                            }
        except:
            pass
        
        # Try CoinCap as second fallback
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"https://api.coincap.io/v2/assets/{symbol.lower()}"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "data" in data:
                            asset_data = data["data"]
                            return {
                                "symbol": symbol,
                                "current_price": float(asset_data.get("priceUsd", 0)),
                                "price_change_24h": float(asset_data.get("changePercent24Hr", 0)),
                                "last_updated": datetime.now().isoformat()
                            }
        except:
            pass
        
        # Try CryptoCompare as third fallback
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"https://min-api.cryptocompare.com/data/price?fsym={symbol.upper()}&tsyms=USD"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "USD" in data:
                            return {
                                "symbol": symbol,
                                "current_price": data["USD"],
                                "price_change_24h": 0.0,  # CryptoCompare doesn't provide 24h change in this endpoint
                                "last_updated": datetime.now().isoformat()
                            }
        except:
            pass
        
        return None

    async def _fetch_alpha_vantage_fallback(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch real-time stock data from multiple sources as fallback"""
        # Try Alpha Vantage first
        try:
            import aiohttp
            # Remove .NS suffix for Alpha Vantage
            clean_symbol = symbol.replace('.NS', '').replace('.NSE', '')
            
            async with aiohttp.ClientSession() as session:
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={clean_symbol}&apikey=demo"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        quote = data.get("Global Quote", {})
                        if quote and quote.get("05. price"):
                            price = float(quote.get("05. price", 0))
                            change = float(quote.get("09. change", 0))
                            change_percent = float(quote.get("10. change percent", "0%").replace("%", ""))
                            
                            return {
                                "symbol": symbol,
                                "current_price": price,
                                "price_change_24h": change_percent,
                                "last_updated": datetime.now().isoformat()
                            }
        except:
            pass
        
        # Try Yahoo Finance as second fallback
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                # Try different Yahoo Finance endpoints
                urls = [
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                    f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}",
                    f"https://query2.finance.yahoo.com/v1/finance/search?q={symbol}"
                ]
                
                for url in urls:
                    try:
                        async with session.get(url, timeout=10) as response:
                            if response.status == 200:
                                data = await response.json()
                                # Parse different Yahoo Finance response formats
                                price = self._extract_yahoo_price(data)
                                if price and price > 0:
                                    return {
                                        "symbol": symbol,
                                        "current_price": price,
                                        "price_change_24h": 0.0,  # Yahoo doesn't always provide 24h change in these endpoints
                                        "last_updated": datetime.now().isoformat()
                                    }
                    except:
                        continue
        except:
            pass
        
        return None

    def _extract_yahoo_price(self, data: dict) -> Optional[float]:
        """Extract price from Yahoo Finance response"""
        try:
            # Try chart data format
            if "chart" in data and "result" in data["chart"]:
                result = data["chart"]["result"][0]
                if "meta" in result and "regularMarketPrice" in result["meta"]:
                    return float(result["meta"]["regularMarketPrice"])
            
            # Try quote data format
            if "quoteResponse" in data and "result" in data["quoteResponse"]:
                result = data["quoteResponse"]["result"][0]
                if "regularMarketPrice" in result:
                    return float(result["regularMarketPrice"])
            
            # Try search data format
            if "quotes" in data and len(data["quotes"]) > 0:
                quote = data["quotes"][0]
                if "regularMarketPrice" in quote:
                    return float(quote["regularMarketPrice"])
        except:
            pass
        return None

    def _get_fallback_indian_stock_data(self) -> List[Dict[str, Any]]:
        """Fallback Indian stock data when real API fails - only used for initial load"""
        return []

    async def get_market_data(self, market_type: str = 'all') -> Dict[str, List[Dict[str, Any]]]:
        """Get market data for specified type(s)"""
        cache_key = f"market_data_{market_type}"
        
        # Check cache first
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        result = {}
        
        if market_type in ['all', 'crypto']:
            # Use CoinGecko for real INR crypto data
            crypto_data = await self.fetch_coingecko_data()
            result['crypto'] = crypto_data
        
        if market_type in ['all', 'stock']:
            # Fetch Indian stock data
            stock_data = await self.fetch_alpha_vantage_data()
            result['stock'] = stock_data
        
        # Update cache
        self._update_cache(cache_key, result)
        
        return result

    async def get_instrument_data(self, symbol: str, market_type: str) -> Optional[Dict[str, Any]]:
        """Get specific instrument data"""
        try:
            market_data = await self.get_market_data(market_type)
        
            for market_key, instruments in market_data.items():
                for instrument in instruments:
                    instrument_symbol = instrument.get('symbol', '')
                    
                    # Exact match
                    if instrument_symbol == symbol:
                        return instrument
                    
                    # Try different symbol formats
                    if market_type == "stock":
                        # For stocks, try without .NS suffix
                        if symbol.endswith('.NS') and instrument_symbol == symbol.replace('.NS', ''):
                            return instrument
                        # Try with .NS suffix
                        if not symbol.endswith('.NS') and instrument_symbol == f"{symbol}.NS":
                            return instrument
                        # Try with .NSE suffix
                        if not symbol.endswith('.NSE') and instrument_symbol == f"{symbol}.NSE":
                            return instrument
        
            return None
            
        except Exception as e:
            return None

    async def refresh_cache(self):
        """Force refresh of all cached data"""
        self.cache.clear()
        self.cache_expiry.clear()
        await self.get_market_data('all')

# Global instance
market_data_service = MarketDataService()