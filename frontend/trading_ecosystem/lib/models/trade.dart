enum TradeSide { buy, sell }
enum TradeStatus { open, closed, cancelled }

class Trade {
  final String tradeId;
  final String userId;
  final String accountId;
  final String instrument;
  final TradeSide side;
  final double quantity;
  final double entryPrice;
  final double? stopLoss;
  final double? takeProfit;
  final TradeStatus status;
  final DateTime timestamp;
  final DateTime? closedAt;
  final double? pnl;
  final Map<String, dynamic>? metadata;

  Trade({
    required this.tradeId,
    required this.userId,
    required this.accountId,
    required this.instrument,
    required this.side,
    required this.quantity,
    required this.entryPrice,
    this.stopLoss,
    this.takeProfit,
    required this.status,
    required this.timestamp,
    this.closedAt,
    this.pnl,
    this.metadata,
  });

  factory Trade.fromJson(Map<String, dynamic> json) {
    return Trade(
      tradeId: json['trade_id'] ?? '',
      userId: json['user_id'] ?? '',
      accountId: json['account_id'] ?? '',
      instrument: json['instrument'] ?? '',
      side: TradeSide.values.firstWhere(
        (e) => e.name == json['side'],
        orElse: () => TradeSide.buy,
      ),
      quantity: (json['quantity'] ?? 0.0).toDouble(),
      entryPrice: (json['entry_price'] ?? 0.0).toDouble(),
      stopLoss: json['stop_loss'] != null ? (json['stop_loss'] as num).toDouble() : null,
      takeProfit: json['take_profit'] != null ? (json['take_profit'] as num).toDouble() : null,
      status: TradeStatus.values.firstWhere(
        (e) => e.name == json['status'],
        orElse: () => TradeStatus.open,
      ),
      timestamp: DateTime.parse(json['timestamp'] ?? DateTime.now().toIso8601String()),
      closedAt: json['closed_at'] != null 
          ? DateTime.parse(json['closed_at']) 
          : null,
      pnl: json['pnl'] != null ? (json['pnl'] as num).toDouble() : null,
      metadata: json['metadata'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'trade_id': tradeId,
      'user_id': userId,
      'account_id': accountId,
      'instrument': instrument,
      'side': side.name,
      'quantity': quantity,
      'entry_price': entryPrice,
      'stop_loss': stopLoss,
      'take_profit': takeProfit,
      'status': status.name,
      'timestamp': timestamp.toIso8601String(),
      'closed_at': closedAt?.toIso8601String(),
      'pnl': pnl,
      'metadata': metadata,
    };
  }

  Trade copyWith({
    String? tradeId,
    String? userId,
    String? accountId,
    String? instrument,
    TradeSide? side,
    double? quantity,
    double? entryPrice,
    double? stopLoss,
    double? takeProfit,
    TradeStatus? status,
    DateTime? timestamp,
    DateTime? closedAt,
    double? pnl,
    Map<String, dynamic>? metadata,
  }) {
    return Trade(
      tradeId: tradeId ?? this.tradeId,
      userId: userId ?? this.userId,
      accountId: accountId ?? this.accountId,
      instrument: instrument ?? this.instrument,
      side: side ?? this.side,
      quantity: quantity ?? this.quantity,
      entryPrice: entryPrice ?? this.entryPrice,
      stopLoss: stopLoss ?? this.stopLoss,
      takeProfit: takeProfit ?? this.takeProfit,
      status: status ?? this.status,
      timestamp: timestamp ?? this.timestamp,
      closedAt: closedAt ?? this.closedAt,
      pnl: pnl ?? this.pnl,
      metadata: metadata ?? this.metadata,
    );
  }

  bool get isOpen => status == TradeStatus.open;
  bool get isClosed => status == TradeStatus.closed;
  bool get isCancelled => status == TradeStatus.cancelled;
  bool get isLong => side == TradeSide.buy;
  bool get isShort => side == TradeSide.sell;

  double get totalValue => quantity * entryPrice;
  double get absolutePnl => pnl?.abs() ?? 0.0;
  bool get isProfitable => pnl != null && pnl! > 0;

  @override
  String toString() {
    return 'Trade(tradeId: $tradeId, instrument: $instrument, side: $side, quantity: $quantity, entryPrice: $entryPrice, status: $status)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is Trade && other.tradeId == tradeId;
  }

  @override
  int get hashCode => tradeId.hashCode;
}
