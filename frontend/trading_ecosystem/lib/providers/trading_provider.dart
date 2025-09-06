import 'package:flutter/foundation.dart';
import 'dart:async';
import '../models/instrument.dart';
import '../models/order.dart';
import '../models/position.dart';
import '../services/trading_service.dart';
import '../services/websocket_service.dart';
import '../services/api_service.dart';

class TradingProvider with ChangeNotifier {
  // State variables
  List<Instrument> _instruments = [];
  List<Instrument> _marketData = [];
  List<Order> _userOrders = [];
  List<Position> _userPositions = [];
  Map<String, dynamic>? _dashboardSummary;
  bool _isLoading = false;
  String? _error;
  String _selectedTvSymbol = "BINANCE:BTCUSDT";
  String _selectedInterval = "60";
  String? _selectedInstrumentId;
  
  // Real-time data state
  final Map<String, double> _livePrices = {};
  bool _isRealTimeEnabled = false;
  
  // Auto-refresh timers
  Timer? _positionRefreshTimer;
  Timer? _pnlRefreshTimer;
  
  // Background refresh state
  bool _isBackgroundRefreshing = false;
  
  // WebSocket service
  final WebSocketService _webSocketService = WebSocketService.instance;
  StreamSubscription? _marketDataSubscription;
  StreamSubscription? _orderDataSubscription;
  StreamSubscription? _positionDataSubscription;
  StreamSubscription? _balanceDataSubscription;
  StreamSubscription? _tradeDataSubscription;
  
  // Account balance state
  Map<String, dynamic>? _accountBalance;
  double _totalEquity = 0.0;
  double _unrealizedPnl = 0.0;
  double _realizedPnl = 0.0;

  // Getters
  List<Instrument> get instruments => _instruments;
  List<Instrument> get marketData => _marketData;
  List<Order> get userOrders => _userOrders;
  List<Position> get userPositions => _userPositions;
  Map<String, dynamic>? get dashboardSummary => _dashboardSummary;
  bool get isLoading => _isLoading;
  String? get error => _error;
  
  // TradingView getters
  String get selectedTvSymbol => _selectedTvSymbol;
  String get selectedInterval => _selectedInterval;
  String? get selectedInstrumentId => _selectedInstrumentId;
  
  // Real-time getters
  Map<String, double> get livePrices => _livePrices;
  bool get isRealTimeEnabled => _isRealTimeEnabled;
  
  // WebSocket getters
  bool get isWebSocketConnected => _webSocketService.isConnected;
  
  // Account balance getters
  Map<String, dynamic>? get accountBalance => _accountBalance;
  double get totalEquity => _totalEquity;
  double get unrealizedPnl => _unrealizedPnl;
  double get realizedPnl => _realizedPnl;

  // Helper getters
  List<Instrument> getInstrumentsByType(String type) {
    return _instruments.where((instrument) => 
      instrument.type.value.toLowerCase() == type.toLowerCase()
    ).toList();
  }

  List<Position> getOpenPositions() {
    return _userPositions.where((position) => 
      position.status == PositionStatus.OPEN
    ).toList();
  }

  List<Position> getClosedPositions() {
    return _userPositions.where((position) => 
      position.status == PositionStatus.CLOSED
    ).toList();
  }

  List<Order> getPendingOrders() {
    return _userOrders.where((order) => 
      order.status == OrderStatus.PENDING
    ).toList();
  }

  String get currency => _accountBalance?['currency'] ?? 'INR';

  // Get live price for a symbol
  double? getLivePrice(String symbol) {
    return _livePrices[symbol];
  }

  // Set loading state
  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  // Set error state
  void _setError(String? error) {
    _error = error;
    notifyListeners();
  }

  // Load initial data
  Future<void> loadInitialData({String? userId}) async {
    try {
      _setLoading(true);
      await Future.wait([
        loadInstruments(),
        loadMarketData(),
        loadUserOrdersData(),
        loadUserPositionsData(),
      ]);
      
      // Connect to WebSocket for real-time data
      await connectWebSocket(userId: userId);
      
      _setError(null);
    } catch (e) {
      _setError('Failed to load initial data: $e');
    } finally {
      _setLoading(false);
    }
  }

  // Load instruments
  Future<void> loadInstruments({String? type}) async {
    try {
      _setLoading(true);
      
      // Load from our backend market data service
      _instruments = await TradingService.getInstruments(type: type);
      
      _setError(null);
    } catch (e) {
      _setError('Failed to load instruments: $e');
    } finally {
      _setLoading(false);
    }
  }

  // Load market data
  Future<void> loadMarketData() async {
    try {
      _setLoading(true);
      
      // Load from our backend market data service
      _marketData = await TradingService.getMarketData();
      
      _setError(null);
    } catch (e) {
      _setError('Failed to load market data: $e');
    } finally {
      _setLoading(false);
    }
  }

  // Refresh market data (for periodic updates)
  Future<void> refreshMarketData() async {
    try {
      await loadMarketData();
      notifyListeners();
    } catch (e) {
      print('Error refreshing market data: $e');
    }
  }

  // Load user orders
  Future<void> loadUserOrders(String token) async {
    try {
      _setLoading(true);
      _userOrders = await TradingService.getUserOrders('user', token);
      _setError(null);
    } catch (e) {
      _setError('Failed to load user orders: $e');
    } finally {
      _setLoading(false);
    }
  }

  // Load user positions
  Future<void> loadUserPositions(String token) async {
    try {
      _setLoading(true);
      _userPositions = await TradingService.getUserPositions('user', token);
      _setError(null);
    } catch (e) {
      _setError('Failed to load user positions: $e');
    } finally {
      _setLoading(false);
    }
  }

  // Load dashboard summary
  Future<void> loadDashboardSummary(String token) async {
    try {
      _setLoading(true);
      _dashboardSummary = await TradingService.getDashboardSummary(token);
      _setError(null);
    } catch (e) {
      _setError('Failed to load dashboard summary: $e');
    } finally {
      _setLoading(false);
    }
  }

  // Load user balance for current active challenge
  Future<void> loadUserBalance() async {
    try {
      print('TradingProvider: Starting to load user balance...');
      _setLoading(true);
      final balanceData = await TradingService.getUserBalance();
      print('TradingProvider: Balance data received: $balanceData');
      _dashboardSummary = balanceData;
      _updateAccountBalance(balanceData);
      _setError(null);
      print('TradingProvider: Balance loaded successfully');
    } catch (e) {
      print('TradingProvider: Error loading balance: $e');
      _setError('Failed to load user balance: $e');
    } finally {
      _setLoading(false);
    }
  }

  // Load user orders
  Future<void> loadUserOrdersData() async {
    try {
      print('TradingProvider: Loading user orders...');
      final orders = await TradingService.getUserOrdersData();
      _userOrders = orders;
      print('TradingProvider: Loaded ${orders.length} orders');
    } catch (e) {
      print('TradingProvider: Error loading orders: $e');
      _setError('Failed to load user orders: $e');
    }
  }

  // Load user positions
  Future<void> loadUserPositionsData() async {
    try {
      print('TradingProvider: Loading user positions...');
      final positions = await TradingService.getUserPositionsData();
      _userPositions = positions;
      print('TradingProvider: Loaded ${positions.length} positions');
      
      // Recalculate total equity and P&L after loading positions
      _updateTotalEquity();
      notifyListeners();
    } catch (e) {
      print('TradingProvider: Error loading positions: $e');
      _setError('Failed to load user positions: $e');
    }
  }

  // TradingView methods
  void setTvSymbol(String tvSymbol) {
    if (_selectedTvSymbol == tvSymbol) return;
    _selectedTvSymbol = tvSymbol;
    notifyListeners();
  }

  void setInterval(String interval) {
    if (_selectedInterval == interval) return;
    _selectedInterval = interval;
    notifyListeners();
  }

  void setSelectedInstrument(String? instrumentId) {
    _selectedInstrumentId = instrumentId;
    if (instrumentId != null) {
      final instrument = _instruments.firstWhere(
        (i) => i.instrumentId == instrumentId,
        orElse: () => _instruments.first,
      );
      if (instrument.tvSymbol != null) {
        setTvSymbol(instrument.tvSymbol!);
      } else {
        setTvSymbol(inferTvSymbol(
          symbol: instrument.symbol,
          type: instrument.type.value,
        ));
      }
    }
    notifyListeners();
  }

  // Infer TradingView symbol if not provided
  String inferTvSymbol({required String symbol, required String type}) {
    final normalized = symbol.replaceAll('/', '').toUpperCase();
    
    if (type.toLowerCase() == 'crypto') {
      return 'BINANCE:${normalized}USDT';
    } else if (type.toLowerCase() == 'stock') {
      return 'NASDAQ:$normalized';
    }
    
    // Fallback to Binance for crypto
    return 'BINANCE:${normalized}USDT';
  }

  // Real-time data methods
  void enableRealTimeData() {
    _isRealTimeEnabled = true;
    _startRealTimeUpdates();
    _startAutoRefreshTimers();
    notifyListeners();
  }

  void disableRealTimeData() {
    _isRealTimeEnabled = false;
    _stopRealTimeUpdates();
    _stopAutoRefreshTimers();
    notifyListeners();
  }
  
  // WebSocket connection methods
  Future<void> connectWebSocket({String? userId}) async {
    try {
      await _webSocketService.connect(userId: userId);
      _setupWebSocketListeners();
      
      // Enable real-time data and auto-refresh when WebSocket connects
      enableRealTimeData();
      
      notifyListeners();
      debugPrint('✅ WebSocket connected in TradingProvider');
    } catch (e) {
      debugPrint('❌ Failed to connect WebSocket: $e');
      _setError('Failed to connect to real-time data: $e');
    }
  }
  
  Future<void> disconnectWebSocket() async {
    await _webSocketService.disconnect();
    _cleanupWebSocketListeners();
    notifyListeners();
    debugPrint('🔌 WebSocket disconnected in TradingProvider');
  }
  
  void _setupWebSocketListeners() {
    // Listen to market data updates
    _marketDataSubscription = _webSocketService.marketDataStream.listen(
      _handleMarketDataUpdate,
      onError: (error) => debugPrint('Market data stream error: $error'),
    );
    
    // Listen to order updates
    _orderDataSubscription = _webSocketService.orderDataStream.listen(
      _handleOrderUpdate,
      onError: (error) => debugPrint('Order data stream error: $error'),
    );
    
    // Listen to position updates
    _positionDataSubscription = _webSocketService.positionDataStream.listen(
      _handlePositionUpdate,
      onError: (error) => debugPrint('Position data stream error: $error'),
    );
    
    // Listen to balance updates
    _balanceDataSubscription = _webSocketService.balanceDataStream.listen(
      _handleBalanceUpdate,
      onError: (error) => debugPrint('Balance data stream error: $error'),
    );
    
    // Listen to trade updates
    _tradeDataSubscription = _webSocketService.tradeDataStream.listen(
      _handleTradeUpdate,
      onError: (error) => debugPrint('Trade data stream error: $error'),
    );
  }
  
  void _cleanupWebSocketListeners() {
    _marketDataSubscription?.cancel();
    _orderDataSubscription?.cancel();
    _positionDataSubscription?.cancel();
    _balanceDataSubscription?.cancel();
    _tradeDataSubscription?.cancel();
    
    _marketDataSubscription = null;
    _orderDataSubscription = null;
    _positionDataSubscription = null;
    _balanceDataSubscription = null;
    _tradeDataSubscription = null;
  }
  
  void _handleMarketDataUpdate(Map<String, dynamic> data) {
    final String type = data['type'] ?? '';
    
    switch (type) {
      case 'initial_market_data':
      case 'market_data_snapshot':
        final marketPrices = data['market_prices'] as Map<String, dynamic>?;
        if (marketPrices != null) {
          _updateLivePrices(marketPrices);
        }
        break;
      case 'price_update':
        final symbol = data['instrument'] as String?;
        final price = data['price'] as double?;
        if (symbol != null && price != null) {
          _livePrices[symbol] = price;
          notifyListeners();
        }
        break;
    }
  }
  
  void _handleOrderUpdate(Map<String, dynamic> data) {
    final String type = data['type'] ?? '';
    final orderData = data['order'] as Map<String, dynamic>?;
    
    if (orderData != null) {
      final order = Order.fromJson(orderData);
      
      switch (type) {
        case 'order_filled':
        case 'order_partially_filled':
          // Update existing order or add new one
          final existingIndex = _userOrders.indexWhere((o) => o.orderId == order.orderId);
          if (existingIndex >= 0) {
            _userOrders[existingIndex] = order;
          } else {
            _userOrders.add(order);
          }
          break;
        case 'order_cancelled':
        case 'order_rejected':
          _userOrders.removeWhere((o) => o.orderId == order.orderId);
          break;
      }
      
      notifyListeners();
    }
  }
  
  void _handlePositionUpdate(Map<String, dynamic> data) {
    final String type = data['type'] ?? '';
    final positionData = data['position'] as Map<String, dynamic>?;
    
    if (positionData != null) {
      final position = Position.fromJson(positionData);
      
      switch (type) {
        case 'position_opened':
        case 'position_updated':
          // Update existing position or add new one
          final existingIndex = _userPositions.indexWhere((p) => p.positionId == position.positionId);
          if (existingIndex >= 0) {
            _userPositions[existingIndex] = position;
          } else {
            _userPositions.add(position);
          }
          break;
        case 'position_closed':
        case 'position_liquidated':
          _userPositions.removeWhere((p) => p.positionId == position.positionId);
          break;
      }
      
      // Recalculate total equity and P&L
      _updateTotalEquity();
      notifyListeners();
    }
  }
  
  void _handleBalanceUpdate(Map<String, dynamic> data) {
    final String type = data['type'] ?? '';
    
    switch (type) {
      case 'account_snapshot':
        final account = data['account'] as Map<String, dynamic>?;
        if (account != null) {
          _updateAccountBalance(account);
        }
        break;
      case 'balance_update':
        final balanceData = data['balance_data'] as Map<String, dynamic>?;
        if (balanceData != null) {
          _updateAccountBalance(balanceData);
        }
        break;
    }
  }
  
  void _handleTradeUpdate(Map<String, dynamic> data) {
    // Handle trade execution updates
    debugPrint('Trade executed: ${data['trade']}');
    notifyListeners();
  }
  
  void _updateLivePrices(Map<String, dynamic> marketPrices) {
    marketPrices.forEach((symbol, priceData) {
      if (priceData is Map<String, dynamic>) {
        final price = priceData['price'] as double?;
        if (price != null) {
          _livePrices[symbol] = price;
        }
      }
    });
    notifyListeners();
  }
  
  void _updateAccountBalance(Map<String, dynamic> balanceData) {
    _accountBalance = balanceData;
    _totalEquity = (balanceData['equity'] as num?)?.toDouble() ?? 0.0;
    _unrealizedPnl = (balanceData['unrealized_pnl'] as num?)?.toDouble() ?? 0.0;
    _realizedPnl = (balanceData['realized_pnl'] as num?)?.toDouble() ?? 0.0;
    // Don't call notifyListeners() here - let the caller decide when to notify
  }
  
  /// Calculate total unrealized P&L from all open positions
  /// This just sums up the P&L values calculated by the backend
  double _calculateTotalUnrealizedPnl() {
    double totalPnl = 0.0;
    for (final position in _userPositions) {
      if (position.status == PositionStatus.OPEN && position.unrealizedPnl != null) {
        // Validate P&L value to prevent extremely large numbers
        final pnl = position.unrealizedPnl!;
        if (pnl.isFinite && pnl.abs() < 1000000) { // Cap at 1M to prevent display issues
          totalPnl += pnl;
        }
      }
    }
    return totalPnl;
  }
  
  /// Update total equity based on available balance + unrealized P&L
  void _updateTotalEquity() {
    final availableBalance = _accountBalance?['available_balance'] ?? 
                           _accountBalance?['balance'] ?? 0.0;
    final totalUnrealizedPnl = _calculateTotalUnrealizedPnl();
    _totalEquity = (availableBalance as num).toDouble() + totalUnrealizedPnl;
    _unrealizedPnl = totalUnrealizedPnl;
    // Don't call notifyListeners() here - let the caller decide when to notify
  }

  void _startRealTimeUpdates() {
    if (!_isRealTimeEnabled) return;
    
    // Real-time updates every 3 seconds for live trading
    Future.delayed(const Duration(seconds: 3), () {
      if (_isRealTimeEnabled && !_isBackgroundRefreshing) {
        _isBackgroundRefreshing = true;
        
        // Sequential updates to avoid race conditions
        _updateAllLivePrices().then((_) {
          return _refreshPositionDataBackground();
        }).then((_) {
          return _triggerPositionPriceUpdate();
        }).then((_) {
          _isBackgroundRefreshing = false;
          _startRealTimeUpdates();
        }).catchError((error) {
          _isBackgroundRefreshing = false;
          debugPrint('Error in real-time updates: $error');
          _startRealTimeUpdates(); // Continue updates even on error
        });
      } else if (_isRealTimeEnabled) {
        // If already refreshing, just restart the timer
        _startRealTimeUpdates();
      }
    });
  }
  
  /// Refresh position data to get updated P&L values
  Future<void> _refreshPositionData() async {
    try {
      final positions = await TradingService.getUserPositionsData();
      _userPositions = positions;
      _updateTotalEquity();
      notifyListeners();
    } catch (e) {
      debugPrint('Error refreshing position data: $e');
    }
  }
  
  /// Background refresh position data (no loading state, no UI glitch, no console spam)
  Future<void> _refreshPositionDataBackground() async {
    try {
      final positions = await TradingService.getUserPositionsData();
      _userPositions = positions;
      
      // Update total equity with new position data
      _updateTotalEquity();
      
      // Notify listeners to update UI with new P&L values
      notifyListeners();
    } catch (e) {
      // Silent error handling - no console spam
      debugPrint('Background position refresh error: $e');
    }
  }
  
  /// Background load user balance (no loading state, no UI glitch, no console spam)
  Future<void> _loadUserBalanceBackground() async {
    try {
      final balanceData = await TradingService.getUserBalance();
      _dashboardSummary = balanceData;
      _updateAccountBalance(balanceData);
      // Only notify listeners once at the end, no loading state changes
      notifyListeners();
    } catch (e) {
      // Silent error handling - no console spam
    }
  }
  
  /// Manually trigger position price updates
  Future<void> refreshPositionPrices() async {
    try {
      final apiService = ApiService();
      final token = await apiService.getToken();
      
      if (token != null) {
        await TradingService.updatePositionPrices(token);
        // Refresh position data after updating prices
        await _refreshPositionData();
      }
    } catch (e) {
      debugPrint('Error refreshing position prices: $e');
    }
  }
  
  /// Trigger backend position price updates (internal method)
  Future<void> _triggerPositionPriceUpdate() async {
    try {
      final apiService = ApiService();
      final token = await apiService.getToken();
      
      if (token != null) {
        await TradingService.updatePositionPrices(token);
      }
    } catch (e) {
      debugPrint('Error triggering position price update: $e');
    }
  }

  void _stopRealTimeUpdates() {
    // Stop real-time updates
  }
  
  /// Start auto-refresh timers for positions and P&L
  void _startAutoRefreshTimers() {
    // Auto-refresh P&L every 2 seconds
    _pnlRefreshTimer = Timer.periodic(const Duration(seconds: 2), (timer) {
      if (_isRealTimeEnabled) {
        _autoRefreshPnl();
      }
    });
    
    debugPrint('🔄 Auto-refresh timers started');
  }
  
  /// Stop auto-refresh timers
  void _stopAutoRefreshTimers() {
    _positionRefreshTimer?.cancel();
    _pnlRefreshTimer?.cancel();
    _positionRefreshTimer = null;
    _pnlRefreshTimer = null;
    
    debugPrint('🛑 Auto-refresh timers stopped');
  }
  
  /// Auto-refresh positions immediately after order placement
  Future<void> _autoRefreshPositionsAfterOrder() async {
    if (_isBackgroundRefreshing) return; // Prevent multiple simultaneous refreshes
    
    try {
      _isBackgroundRefreshing = true;
      debugPrint('🔄 Auto-refreshing positions after order placement...');
      
      // Wait for backend to process the order (increased delay)
      await Future.delayed(const Duration(milliseconds: 1500));
      
      // Refresh positions data (background, no loading state)
      await _refreshPositionDataBackground();
      
      // Also refresh balance to get updated P&L (background, no loading state)
      await _loadUserBalanceBackground();
      
      debugPrint('✅ Positions auto-refreshed after order');
    } catch (e) {
      debugPrint('❌ Error auto-refreshing positions after order: $e');
    } finally {
      _isBackgroundRefreshing = false;
    }
  }
  
  /// Auto-refresh P&L every 2 seconds (silent background refresh)
  Future<void> _autoRefreshPnl() async {
    if (_isBackgroundRefreshing) return; // Prevent multiple simultaneous refreshes
    
    try {
      _isBackgroundRefreshing = true;
      
      // Refresh position prices in backend (background, no console spam)
      await _triggerPositionPriceUpdate();
      
      // Refresh position data to get updated P&L (background, no loading state)
      await _refreshPositionDataBackground();
      
      // Refresh balance to get updated total equity (background, no loading state)
      await _loadUserBalanceBackground();
      
    } catch (e) {
      // Silent error handling - no console spam
    } finally {
      _isBackgroundRefreshing = false;
    }
  }

  Future<void> _updateAllLivePrices() async {
    // Update live prices for all instruments sequentially
    for (final instrument in _instruments) {
      await _updateInstrumentPrice(instrument);
    }
    notifyListeners();
  }

  Future<void> _updateInstrumentPrice(Instrument instrument) async {
    try {
      final livePrice = await TradingService.getLivePrice(
        instrument.symbol,
        instrument.type.value,
      );
      
      if (livePrice != null) {
        _livePrices[instrument.symbol] = livePrice;
      } else {
        // Use fallback price if live price fails
        _livePrices[instrument.symbol] = instrument.currentPrice;
      }
    } catch (e) {
      // Use fallback price on error
      _livePrices[instrument.symbol] = instrument.currentPrice;
      debugPrint('Using fallback price for ${instrument.symbol}: ${instrument.currentPrice}');
    }
  }

  // Place order
  Future<void> placeOrder(Map<String, dynamic> orderData, String token) async {
    try {
      _setLoading(true);
      final newOrder = await TradingService.placeOrder(orderData, token);
      _userOrders.add(newOrder);
      
      // Auto-refresh positions immediately after placing order
      await _autoRefreshPositionsAfterOrder();
      
      _setError(null);
      notifyListeners();
    } catch (e) {
      _setError('Failed to place order: $e');
    } finally {
      _setLoading(false);
    }
  }

  // Cancel order
  Future<void> cancelOrder(String orderId, String token) async {
    try {
      _setLoading(true);
      final success = await TradingService.cancelOrder(orderId, token);
      if (success) {
        _userOrders.removeWhere((order) => order.orderId == orderId);
        notifyListeners();
      }
      _setError(null);
    } catch (e) {
      _setError('Failed to cancel order: $e');
    } finally {
      _setLoading(false);
    }
  }

  // Get historical data
  Future<List<Map<String, dynamic>>> getHistoricalData(String symbol, String interval, String type) async {
    try {
      return await TradingService.getHistoricalData(symbol, interval, type);
    } catch (e) {
      _setError('Failed to get historical data: $e');
      return [];
    }
  }

  // Get market news
  Future<List<Map<String, dynamic>>> getMarketNews() async {
    try {
      return await TradingService.getMarketNews();
    } catch (e) {
      _setError('Failed to get market news: $e');
      return [];
    }
  }

  // Get trading signals
  Future<List<Map<String, dynamic>>> getTradingSignals(String symbol) async {
    try {
      return await TradingService.getTradingSignals(symbol);
    } catch (e) {
      _setError('Failed to get trading signals: $e');
      return [];
    }
  }

  // Close position
  Future<void> closePosition(String positionId, {double? closeQuantity}) async {
    try {
      _setLoading(true);
      _setError(null);
      
      final apiService = ApiService();
      final result = await apiService.closePosition(positionId, closeQuantity: closeQuantity);
      
      if (result.isSuccess) {
        // Remove the position from the list
        _userPositions.removeWhere((position) => position.positionId == positionId);
        
        // Refresh balance to get updated P&L
        await loadUserBalance();
        
        _setError(null);
        notifyListeners();
      } else {
        _setError(result.error ?? 'Failed to close position');
      }
    } catch (e) {
      _setError('Error closing position: $e');
    } finally {
      _setLoading(false);
    }
  }

  // Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }

  // Refresh all data
  Future<void> refreshAllData(String token) async {
    try {
      _setLoading(true);
      await Future.wait([
        loadInstruments(),
        loadMarketData(),
        loadUserOrders(token),
        loadUserPositions(token),
        loadDashboardSummary(token),
      ]);
      _setError(null);
    } catch (e) {
      _setError('Failed to refresh data: $e');
    } finally {
      _setLoading(false);
    }
  }
  
  // Dispose method to clean up resources
  @override
  void dispose() {
    _stopAutoRefreshTimers();
    _cleanupWebSocketListeners();
    _webSocketService.dispose();
    super.dispose();
  }
}
