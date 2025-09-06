import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/instrument.dart';
import '../models/order.dart';
import '../models/position.dart';
import '../services/api_service.dart'; // Added import for ApiService

class TradingService {
  // Base URLs for different APIs
  static const String baseUrl = 'http://localhost:8000/api/v1/trading';
  static const String binanceApiUrl = 'https://api.binance.com/api/v3';
  static const String coinGeckoApiUrl = 'https://api.coingecko.com/api/v3';
  static const String alphaVantageApiUrl = 'https://www.alphavantage.co/query';
  
  // API Keys (should be stored securely in production)
  static const String alphaVantageApiKey = 'demo'; // Replace with real key
  
  // WebSocket connections for real-time data
  static const String binanceWsUrl = 'wss://stream.binance.com:9443/ws';
  
  // Get all instruments with live market data
  static Future<List<Instrument>> getInstruments({String? type}) async {
    try {
      // Use ApiService for better error handling and authentication
      final apiService = ApiService();
      final result = await apiService.getMarketData(marketType: type);
      
      if (result.isSuccess && result.data != null) {
        final Map<String, dynamic> data = result.data!['data'] ?? {};
        List<Instrument> instruments = [];
        
        // Process crypto data
        if (data['crypto'] != null) {
          final List<dynamic> cryptoData = data['crypto'];
          instruments.addAll(cryptoData.map((json) => Instrument.fromMarketData(json)).toList());
        }
        
        // Process stock data
        if (data['stock'] != null) {
          final List<dynamic> stockData = data['stock'];
          instruments.addAll(stockData.map((json) => Instrument.fromMarketData(json)).toList());
        }
        
        if (instruments.isNotEmpty) {
          return instruments;
        }
      }
      
      // Fallback to external APIs if backend fails

      return await _getInstrumentsFromExternalApis(type);
      
    } catch (e) {

      // Return fallback data
      return await _getInstrumentsFromExternalApis(type);
    }
  }

  // Get live market data from external APIs
  static Future<List<Instrument>> _getInstrumentsFromExternalApis(String? type) async {
    try {
      if (type == null || type.toLowerCase() == 'crypto') {
        return await _getCryptoInstruments();
      } else if (type.toLowerCase() == 'stock') {
        return await _getStockInstruments();
      }
      
      // Return both if no type specified
      final crypto = await _getCryptoInstruments();
      final stocks = await _getStockInstruments();
      return [...crypto, ...stocks];
      
    } catch (e) {

      return _getFallbackInstruments();
    }
  }

  // Get crypto instruments from CoinGecko
  static Future<List<Instrument>> _getCryptoInstruments() async {
    try {
      final response = await http.get(
        Uri.parse('$coinGeckoApiUrl/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1&sparkline=false'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => Instrument(
          instrumentId: json['id'],
          symbol: json['symbol'].toUpperCase(),
          name: json['name'],
          type: InstrumentType.CRYPTO,
          currentPrice: json['current_price']?.toDouble() ?? 0.0,
          priceChange24h: json['price_change_percentage_24h']?.toDouble(),
          volume24h: json['total_volume']?.toDouble(),
          marketCap: json['market_cap']?.toDouble(),
          isActive: true,
          lastUpdated: DateTime.now(),
          tvSymbol: 'BINANCE:${json['symbol'].toUpperCase()}USDT',
        )).toList();
      }
    } catch (e) {

    }
    
    return _getFallbackCryptoInstruments();
  }

  // Get stock instruments from Alpha Vantage
  static Future<List<Instrument>> _getStockInstruments() async {
    try {
      final response = await http.get(
        Uri.parse('$alphaVantageApiUrl?function=TOP_GAINERS_LOSERS&apikey=$alphaVantageApiKey'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        final List<dynamic> topGainers = data['top_gainers'] ?? [];
        final List<dynamic> topLosers = data['top_losers'] ?? [];
        
        final allStocks = [...topGainers, ...topLosers];
        
        return allStocks.map((json) => Instrument(
          instrumentId: json['ticker'],
          symbol: json['ticker'],
          name: json['company_name'] ?? json['ticker'],
          type: InstrumentType.STOCK,
          currentPrice: double.tryParse(json['price'] ?? '0') ?? 0.0,
          priceChange24h: double.tryParse(json['change_amount'] ?? '0'),
          volume24h: double.tryParse(json['volume'] ?? '0'),
          marketCap: null,
          isActive: true,
          lastUpdated: DateTime.now(),
          tvSymbol: 'NASDAQ:${json['ticker']}',
        )).toList();
      }
    } catch (e) {

    }
    
    return _getFallbackStockInstruments();
  }

  // Fallback instruments if APIs fail
  static List<Instrument> _getFallbackInstruments() {
    return [
      ..._getFallbackCryptoInstruments(),
      ..._getFallbackStockInstruments(),
    ];
  }

  static List<Instrument> _getFallbackCryptoInstruments() {
    return [
      Instrument(
        instrumentId: 'bitcoin',
        symbol: 'BTC',
        name: 'Bitcoin',
        type: InstrumentType.CRYPTO,
        currentPrice: 45000.0,
        priceChange24h: 2.5,
        volume24h: 25000000000,
        marketCap: 850000000000,
        isActive: true,
        lastUpdated: DateTime.now(),
        tvSymbol: 'BINANCE:BTCUSDT',
      ),
      Instrument(
        instrumentId: 'ethereum',
        symbol: 'ETH',
        name: 'Ethereum',
        type: InstrumentType.CRYPTO,
        currentPrice: 3200.0,
        priceChange24h: 1.8,
        volume24h: 15000000000,
        marketCap: 380000000000,
        isActive: true,
        lastUpdated: DateTime.now(),
        tvSymbol: 'BINANCE:ETHUSDT',
      ),
    ];
  }

  static List<Instrument> _getFallbackStockInstruments() {
    return [
      Instrument(
        instrumentId: 'apple',
        symbol: 'AAPL',
        name: 'Apple Inc.',
        type: InstrumentType.STOCK,
        currentPrice: 175.0,
        priceChange24h: 1.2,
        volume24h: 50000000,
        marketCap: 2750000000000,
        isActive: true,
        lastUpdated: DateTime.now(),
        tvSymbol: 'NASDAQ:AAPL',
      ),
      Instrument(
        instrumentId: 'google',
        symbol: 'GOOGL',
        name: 'Alphabet Inc.',
        type: InstrumentType.STOCK,
        currentPrice: 140.0,
        priceChange24h: -0.8,
        volume24h: 25000000,
        marketCap: 1750000000000,
        isActive: true,
        lastUpdated: DateTime.now(),
        tvSymbol: 'NASDAQ:GOOGL',
      ),
    ];
  }

  // Get real-time market data
  static Future<List<Instrument>> getMarketData() async {
    try {
      // Try backend first
      final response = await http.get(
        Uri.parse('$baseUrl/market-data'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        
        if (data['instruments'] != null) {
          final List<dynamic> instruments = data['instruments'];
          return instruments.map((json) => Instrument.fromJson(json)).toList();
        }
      }
      
      // Fallback to external APIs
      return await _getInstrumentsFromExternalApis(null);
      
    } catch (e) {

      return await _getInstrumentsFromExternalApis(null);
    }
  }

  // Get live price for a specific symbol
  static Future<double?> getLivePrice(String symbol, String type) async {
    try {
      // Use backend API instead of direct external API calls to avoid CORS issues
      final apiService = ApiService();
      final result = await apiService.getInstrumentPrice(symbol, type.toLowerCase());
      
      if (result.isSuccess && result.data != null) {
        final price = result.data!['data']?['current_price'];
        if (price != null) {
          return double.tryParse(price.toString());
        }
      }
      
      // If backend fails, try direct API calls as fallback (will handle CORS gracefully)

      if (type.toLowerCase() == 'crypto') {
        return await _getCryptoPrice(symbol);
      } else if (type.toLowerCase() == 'stock') {
        return await _getStockPrice(symbol);
      }
    } catch (e) {

    }
    return _getFallbackPrice(symbol, type);
  }

  // Get fallback price for any symbol and type
  static double? _getFallbackPrice(String symbol, String type) {
    if (type.toLowerCase() == 'crypto') {
      return _getFallbackCryptoPrice(symbol);
    } else if (type.toLowerCase() == 'stock') {
      return _getFallbackStockPrice(symbol);
    }
    return null;
  }

  // Get crypto price from Binance with proper CORS error handling
  static Future<double?> _getCryptoPrice(String symbol) async {
    try {
      // Add timeout and proper error handling
      final response = await http.get(
        Uri.parse('$binanceApiUrl/ticker/price?symbol=${symbol}USDT'),
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'TradingEcosystem/1.0',
        },
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        return double.tryParse(data['price'] ?? '0');
      } else if (response.statusCode == 400) {
        // Symbol not found, try alternative format
        final altResponse = await http.get(
          Uri.parse('$binanceApiUrl/ticker/price?symbol=${symbol}BTC'),
          headers: {
            'Content-Type': 'application/json',
            'User-Agent': 'TradingEcosystem/1.0',
          },
        ).timeout(const Duration(seconds: 10));
        
        if (altResponse.statusCode == 200) {
          final Map<String, dynamic> altData = json.decode(altResponse.body);
          return double.tryParse(altData['price'] ?? '0');
        }
      }
    } catch (e) {
      // Handle CORS and network errors gracefully
      if (e.toString().contains('Failed to fetch') || 
          e.toString().contains('ClientException') ||
          e.toString().contains('CORS') ||
          e.toString().contains('XMLHttpRequest')) {
        // CORS or network error - use fallback price

        return _getFallbackCryptoPrice(symbol);
      }

    }
    return _getFallbackCryptoPrice(symbol);
  }

  // Get fallback crypto price
  static double? _getFallbackCryptoPrice(String symbol) {
    final fallbackPrices = {
      'BTC': 45000.0,
      'ETH': 3200.0,
      'XRP': 0.5,
      'BNB': 300.0,
      'USDT': 1.0,
      'SOL': 100.0,
      'STETH': 3200.0,
      'DOGE': 0.08,
      'USDC': 1.0,
      'ADA': 0.4,
      'TRX': 0.1,
      'WSTETH': 3200.0,
      'WBETH': 3200.0,
      'LINK': 15.0,
      'WBTC': 45000.0,
      'WETH': 3200.0,
      'SUI': 1.5,
      'AVAX': 25.0,
      'HBAR': 0.05,
      'TON': 2.0,
      'SHIB': 0.00001,
      'DOT': 6.0,
      'UNI': 8.0,
      'NEAR': 3.0,
      'AAVE': 100.0,
      'PEPE': 0.000001,
      'ETC': 20.0,
      'LTC': 70.0,
      'CRO': 0.1,
    };
    
    return fallbackPrices[symbol.toUpperCase()];
  }

  // Get fallback stock price
  static double? _getFallbackStockPrice(String symbol) {
    final fallbackPrices = {
      'AAPL': 175.0,
      'MSFT': 350.0,
      'GOOGL': 140.0,
      'AMZN': 150.0,
      'TSLA': 250.0,
      'META': 300.0,
      'NVDA': 500.0,
      'NFLX': 400.0,
    };
    return fallbackPrices[symbol.toUpperCase()];
  }

  // Get stock price from Alpha Vantage with CORS error handling
  static Future<double?> _getStockPrice(String symbol) async {
    try {
      final response = await http.get(
        Uri.parse('$alphaVantageApiUrl?function=GLOBAL_QUOTE&symbol=$symbol&apikey=$alphaVantageApiKey'),
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        final quote = data['Global Quote'];
        if (quote != null) {
          return double.tryParse(quote['05. price'] ?? '0');
        }
      }
    } catch (e) {
      // Handle CORS and network errors gracefully
      if (e.toString().contains('Failed to fetch') || 
          e.toString().contains('ClientException') ||
          e.toString().contains('CORS') ||
          e.toString().contains('XMLHttpRequest')) {
        // CORS or network error - use fallback price

        return _getFallbackStockPrice(symbol);
      }

    }
    return _getFallbackStockPrice(symbol);
  }

  // Get user orders with authentication
  static Future<List<Order>> getUserOrders(String userId, String token) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/orders'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        final List<dynamic> orders = data['orders'] ?? [];
        return orders.map((json) => Order.fromJson(json)).toList();
      } else {
        throw Exception('Failed to load orders: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error fetching orders: $e');
    }
  }

  // Get user positions with authentication
  static Future<List<Position>> getUserPositions(String userId, String token) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/positions'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        final List<dynamic> positions = data['positions'] ?? [];
        return positions.map((json) => Position.fromJson(json)).toList();
      } else {
        throw Exception('Failed to load positions: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error fetching positions: $e');
    }
  }

  // Get dashboard summary with authentication
  static Future<Map<String, dynamic>> getDashboardSummary(String token) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/dashboard/summary'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        return data['data'] ?? {};
      } else {
        throw Exception('Failed to load dashboard summary: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error fetching dashboard summary: $e');
    }
  }

  // Get user balance for current active challenge
  static Future<Map<String, dynamic>> getUserBalance([int? challengeId]) async {
    try {

      // Import ApiService to use its authentication
      final apiService = ApiService();
      final response = await apiService.getCurrentUserChallengeBalance();
      

      
      if (response.isSuccess) {

        return response.data ?? {};
      } else {
        throw Exception('Failed to load user balance: ${response.error}');
      }
    } catch (e) {

      // Return mock data for now
      return {
        'challenge_id': challengeId ?? 1,
        'initial_balance': 100000.0,
        'available_balance': 95000.0,
        'total_equity': 97500.0,
        'unrealized_pnl': 2500.0,
        'used_margin': 5000.0,
        'currency': 'INR',
        'open_positions_count': 2,
        'pending_orders_count': 1,
        'total_trades': 15,
      };
    }
  }

  // Place a new order with authentication
  static Future<Order> placeOrder(Map<String, dynamic> orderData, String token) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/orders'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: json.encode(orderData),
      );

      if (response.statusCode == 201) {
        final Map<String, dynamic> data = json.decode(response.body);
        return Order.fromJson(data['data'] ?? data);
      } else {
        throw Exception('Failed to place order: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error placing order: $e');
    }
  }

  // Get user orders (overloaded method without parameters)
  static Future<List<Order>> getUserOrdersData() async {
    try {
      final apiService = ApiService();
      final token = await apiService.getToken();
      
      if (token == null) {
        throw Exception('No authentication token found');
      }
      
      final response = await http.get(
        Uri.parse('$baseUrl/orders'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        final List<dynamic> orders = data['orders'] ?? [];
        return orders.map((json) => Order.fromJson(json)).toList();
      } else {
        throw Exception('Failed to load orders: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error fetching orders: $e');
    }
  }

  // Get user positions (overloaded method without parameters)
  static Future<List<Position>> getUserPositionsData() async {
    try {
      final apiService = ApiService();
      final token = await apiService.getToken();
      
      if (token == null) {
        throw Exception('No authentication token found');
      }
      
      final response = await http.get(
        Uri.parse('$baseUrl/positions'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        final List<dynamic> positions = data['positions'] ?? [];
        return positions.map((json) => Position.fromJson(json)).toList();
      } else {
        throw Exception('Failed to load positions: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error fetching positions: $e');
    }
  }

  // Cancel an order with authentication
  static Future<bool> cancelOrder(String orderId, String token) async {
    try {
      final response = await http.delete(
        Uri.parse('$baseUrl/orders/$orderId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      return response.statusCode == 200;
    } catch (e) {
      throw Exception('Error cancelling order: $e');
    }
  }

  // Update position prices with latest market data
  static Future<bool> updatePositionPrices(String token) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/positions/update-prices'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      return response.statusCode == 200;
    } catch (e) {
      throw Exception('Error updating position prices: $e');
    }
  }

  // Get chart data for an instrument
  static Future<List<Map<String, dynamic>>> getChartData(String instrumentId, String token) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/chart/$instrumentId'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        final List<dynamic> chartData = data['data'] ?? [];
        return chartData.cast<Map<String, dynamic>>();
      } else {
        throw Exception('Failed to load chart data: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Error fetching chart data: $e');
    }
  }

  // Get historical data for charting
  static Future<List<Map<String, dynamic>>> getHistoricalData(String symbol, String interval, String type) async {
    try {
      if (type.toLowerCase() == 'crypto') {
        return await _getCryptoHistoricalData(symbol, interval);
      } else if (type.toLowerCase() == 'stock') {
        return await _getStockHistoricalData(symbol, interval);
      }
    } catch (e) {

    }
    return [];
  }

  // Get crypto historical data from Binance
  static Future<List<Map<String, dynamic>>> _getCryptoHistoricalData(String symbol, String interval) async {
    try {
      final response = await http.get(
        Uri.parse('$binanceApiUrl/klines?symbol=${symbol}USDT&interval=$interval&limit=100'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((item) => {
          'timestamp': item[0],
          'open': double.parse(item[1]),
          'high': double.parse(item[2]),
          'low': double.parse(item[3]),
          'close': double.parse(item[4]),
          'volume': double.parse(item[5]),
        }).toList();
      }
    } catch (e) {

    }
    return [];
  }

  // Get stock historical data from Alpha Vantage
  static Future<List<Map<String, dynamic>>> _getStockHistoricalData(String symbol, String interval) async {
    try {
      final function = interval == '1D' ? 'TIME_SERIES_DAILY' : 'TIME_SERIES_INTRADAY';
      final response = await http.get(
        Uri.parse('$alphaVantageApiUrl?function=$function&symbol=$symbol&apikey=$alphaVantageApiKey'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        final timeSeries = data['Time Series (Daily)'] ?? data['Time Series (1min)'] ?? {};
        
        final List<Map<String, dynamic>> result = [];
        for (final entry in timeSeries.entries) {
          final values = entry.value as Map<String, dynamic>;
          result.add({
            'timestamp': DateTime.parse(entry.key).millisecondsSinceEpoch,
            'open': double.parse(values['1. open']),
            'high': double.parse(values['2. high']),
            'low': double.parse(values['3. low']),
            'close': double.parse(values['4. close']),
            'volume': double.parse(values['5. volume']),
          });
        }
        return result;
      }
    } catch (e) {
      print('Error getting stock historical data: $e');
    }
    return [];
  }

  // Get market news and updates
  static Future<List<Map<String, dynamic>>> getMarketNews() async {
    try {
      // This would typically come from a news API like NewsAPI
      // For now, return sample data
      return [
        {
          'title': 'Bitcoin reaches new all-time high',
          'summary': 'Bitcoin has reached a new all-time high of 50,000 USD',
          'source': 'CryptoNews',
          'publishedAt': DateTime.now().toIso8601String(),
          'url': 'https://example.com/news1',
        },
        {
          'title': 'Tech stocks rally on strong earnings',
          'summary': 'Major tech companies report strong quarterly earnings',
          'source': 'MarketWatch',
          'publishedAt': DateTime.now().toIso8601String(),
          'url': 'https://example.com/news2',
        },
      ];
    } catch (e) {
      print('Error getting market news: $e');
      return [];
    }
  }

  // Get trading signals and analysis
  static Future<List<Map<String, dynamic>>> getTradingSignals(String symbol) async {
    try {
      // This would typically come from a technical analysis API
      // For now, return sample signals
      return [
        {
          'symbol': symbol,
          'signal': 'BUY',
          'strength': 'STRONG',
          'reason': 'RSI oversold, MACD bullish crossover',
          'target': '5% above current price',
          'stopLoss': '2% below current price',
          'timestamp': DateTime.now().toIso8601String(),
        },
      ];
    } catch (e) {
      print('Error getting trading signals: $e');
      return [];
    }
  }
}
