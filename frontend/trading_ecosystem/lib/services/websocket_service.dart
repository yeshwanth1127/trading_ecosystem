import 'dart:convert';
import 'dart:async';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as status;
import 'package:flutter/foundation.dart';

class WebSocketService {
  static WebSocketService? _instance;
  static WebSocketService get instance => _instance ??= WebSocketService._();
  
  WebSocketService._();
  
  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  bool _isConnected = false;
  String? _userId;
  Timer? _pingTimer;
  
  // Stream controllers for different data types
  final StreamController<Map<String, dynamic>> _marketDataController = 
      StreamController<Map<String, dynamic>>.broadcast();
  final StreamController<Map<String, dynamic>> _orderDataController = 
      StreamController<Map<String, dynamic>>.broadcast();
  final StreamController<Map<String, dynamic>> _positionDataController = 
      StreamController<Map<String, dynamic>>.broadcast();
  final StreamController<Map<String, dynamic>> _balanceDataController = 
      StreamController<Map<String, dynamic>>.broadcast();
  final StreamController<Map<String, dynamic>> _tradeDataController = 
      StreamController<Map<String, dynamic>>.broadcast();
  
  // Getters for streams
  Stream<Map<String, dynamic>> get marketDataStream => _marketDataController.stream;
  Stream<Map<String, dynamic>> get orderDataStream => _orderDataController.stream;
  Stream<Map<String, dynamic>> get positionDataStream => _positionDataController.stream;
  Stream<Map<String, dynamic>> get balanceDataStream => _balanceDataController.stream;
  Stream<Map<String, dynamic>> get tradeDataStream => _tradeDataController.stream;
  
  bool get isConnected => _isConnected;
  
  /// Connect to the WebSocket server
  Future<void> connect({String? userId}) async {
    if (_isConnected) return;
    
    _userId = userId;
    
    try {
      // Connect to our backend WebSocket endpoint
      _channel = WebSocketChannel.connect(
        Uri.parse('ws://localhost:8000/api/v1/trading-events/stream'),
      );
      
      _subscription = _channel!.stream.listen(
        _handleMessage,
        onError: _handleError,
        onDone: _handleDisconnect,
      );
      
      _isConnected = true;
      _startPingTimer();
      
      debugPrint('✅ WebSocket connected successfully');
      
    } catch (e) {
      debugPrint('❌ WebSocket connection failed: $e');
      _isConnected = false;
      rethrow;
    }
  }
  
  /// Disconnect from the WebSocket server
  Future<void> disconnect() async {
    _stopPingTimer();
    _subscription?.cancel();
    
    try {
      if (_channel != null && _isConnected) {
        await _channel!.sink.close(status.goingAway);
      }
    } catch (e) {
      debugPrint('Error closing WebSocket: $e');
    }
    
    _channel = null;
    _isConnected = false;
    _userId = null;
    
    debugPrint('🔌 WebSocket disconnected');
  }
  
  /// Send a message to the server
  void sendMessage(Map<String, dynamic> message) {
    if (!_isConnected || _channel == null) {
      debugPrint('⚠️ Cannot send message: WebSocket not connected');
      return;
    }
    
    try {
      _channel!.sink.add(json.encode(message));
    } catch (e) {
      debugPrint('❌ Failed to send message: $e');
    }
  }
  
  /// Subscribe to specific event types
  void subscribeToEvents(List<String> eventTypes) {
    sendMessage({
      'type': 'subscribe',
      'events': eventTypes,
    });
  }
  
  /// Request current data snapshot
  void requestDataSnapshot({String? userId}) {
    sendMessage({
      'type': 'request_data',
      'user_id': userId ?? _userId,
    });
  }
  
  /// Send ping to keep connection alive
  void _sendPing() {
    sendMessage({'type': 'ping'});
  }
  
  /// Start ping timer to keep connection alive
  void _startPingTimer() {
    _pingTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      _sendPing();
    });
  }
  
  /// Stop ping timer
  void _stopPingTimer() {
    _pingTimer?.cancel();
    _pingTimer = null;
  }
  
  /// Handle incoming WebSocket messages
  void _handleMessage(dynamic message) {
    try {
      final Map<String, dynamic> data = json.decode(message);
      final String messageType = data['type'] ?? 'unknown';
      
      debugPrint('📨 WebSocket message received: $messageType');
      
      switch (messageType) {
        case 'initial_data':
          _handleInitialData(data);
          break;
        case 'data_snapshot':
          _handleDataSnapshot(data);
          break;
        case 'balance_update':
          _handleBalanceUpdate(data);
          break;
        case 'price_update':
          _handlePriceUpdate(data);
          break;
        case 'order_filled':
        case 'order_partially_filled':
        case 'order_cancelled':
        case 'order_rejected':
          _handleOrderUpdate(data);
          break;
        case 'position_opened':
        case 'position_updated':
        case 'position_closed':
        case 'position_liquidated':
          _handlePositionUpdate(data);
          break;
        case 'trade_executed':
          _handleTradeUpdate(data);
          break;
        case 'pong':
          // Server responded to ping
          break;
        case 'error':
          debugPrint('❌ WebSocket error: ${data['message']}');
          _handleWebSocketError(data['message'] ?? 'Unknown error');
          break;
        default:
          debugPrint('⚠️ Unknown message type: $messageType');
      }
      
    } catch (e) {
      debugPrint('❌ Failed to parse WebSocket message: $e');
      _handleWebSocketError('Message parsing failed: $e');
    }
  }

  /// Handle WebSocket errors with recovery
  void _handleWebSocketError(String error) {
    debugPrint('🔧 WebSocket error detected: $error');
    
    // Attempt reconnection after a delay
    Future.delayed(const Duration(seconds: 5), () {
      if (!_isConnected) {
        debugPrint('🔄 Attempting WebSocket reconnection...');
        _attemptReconnection();
      }
    });
  }

  /// Attempt to reconnect WebSocket
  Future<void> _attemptReconnection() async {
    try {
      await disconnect();
      await Future.delayed(const Duration(seconds: 2));
      await connect(userId: _userId);
      debugPrint('✅ WebSocket reconnection successful');
    } catch (e) {
      debugPrint('❌ WebSocket reconnection failed: $e');
      // Schedule another reconnection attempt
      Future.delayed(const Duration(seconds: 10), () {
        if (!_isConnected) {
          _attemptReconnection();
        }
      });
    }
  }
  
  /// Handle initial data message
  void _handleInitialData(Map<String, dynamic> data) {
    final marketPrices = data['market_prices'] as Map<String, dynamic>?;
    if (marketPrices != null) {
      _marketDataController.add({
        'type': 'initial_market_data',
        'market_prices': marketPrices,
        'timestamp': data['timestamp'],
      });
    }
  }
  
  /// Handle data snapshot message
  void _handleDataSnapshot(Map<String, dynamic> data) {
    // Market prices
    final marketPrices = data['market_prices'] as Map<String, dynamic>?;
    if (marketPrices != null) {
      _marketDataController.add({
        'type': 'market_data_snapshot',
        'market_prices': marketPrices,
        'timestamp': data['timestamp'],
      });
    }
    
    // Orders
    final orders = data['orders'] as List<dynamic>?;
    if (orders != null) {
      _orderDataController.add({
        'type': 'orders_snapshot',
        'orders': orders,
        'timestamp': data['timestamp'],
      });
    }
    
    // Positions
    final positions = data['positions'] as List<dynamic>?;
    if (positions != null) {
      _positionDataController.add({
        'type': 'positions_snapshot',
        'positions': positions,
        'timestamp': data['timestamp'],
      });
    }
    
    // Account data
    final account = data['account'] as Map<String, dynamic>?;
    if (account != null) {
      _balanceDataController.add({
        'type': 'account_snapshot',
        'account': account,
        'timestamp': data['timestamp'],
      });
    }
  }
  
  /// Handle balance update message
  void _handleBalanceUpdate(Map<String, dynamic> data) {
    _balanceDataController.add({
      'type': 'balance_update',
      'user_id': data['user_id'],
      'account_id': data['account_id'],
      'balance_data': data['balance_data'],
      'timestamp': data['timestamp'],
    });
  }
  
  /// Handle price update message
  void _handlePriceUpdate(Map<String, dynamic> data) {
    _marketDataController.add({
      'type': 'price_update',
      'instrument': data['instrument'],
      'price': data['price'],
      'bid': data['bid'],
      'ask': data['ask'],
      'volume': data['volume'],
      'timestamp': data['timestamp'],
    });
  }
  
  /// Handle order update message
  void _handleOrderUpdate(Map<String, dynamic> data) {
    _orderDataController.add({
      'type': data['type'],
      'order': data['order'],
      'timestamp': data['timestamp'],
    });
  }
  
  /// Handle position update message
  void _handlePositionUpdate(Map<String, dynamic> data) {
    _positionDataController.add({
      'type': data['type'],
      'position': data['position'],
      'timestamp': data['timestamp'],
    });
  }
  
  /// Handle trade update message
  void _handleTradeUpdate(Map<String, dynamic> data) {
    _tradeDataController.add({
      'type': 'trade_executed',
      'trade': data['trade'],
      'timestamp': data['timestamp'],
    });
  }
  
  /// Handle WebSocket errors
  void _handleError(error) {
    debugPrint('❌ WebSocket error: $error');
    _isConnected = false;
  }
  
  /// Handle WebSocket disconnection
  void _handleDisconnect() {
    debugPrint('🔌 WebSocket disconnected');
    _isConnected = false;
    _stopPingTimer();
    
    // Don't try to close the channel again if it's already closed
    _channel = null;
  }
  
  /// Dispose of resources
  void dispose() {
    disconnect();
    _marketDataController.close();
    _orderDataController.close();
    _positionDataController.close();
    _balanceDataController.close();
    _tradeDataController.close();
  }
}
